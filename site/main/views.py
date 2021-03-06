"""
 This file was created on October 15th, 2016
 by Deborah Venuti, Bethany Sanders and James Riley

 Contributors: Deborah Venuti, Bethany Sanders,
  James Riley, Gene Ryasnianskiy, Alexander Sumner

Last updated on: November 30, 2016
Updated by: Alexander Sumner
"""

#Python Imports
import tarfile
import os

#Django Imports
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files import File
from django.shortcuts import render, render_to_response, reverse
from django.shortcuts import get_object_or_404
from django.views.generic.edit import FormView
from stegasaurus.settings import MEDIA_ROOT

#App Imports
from .models import stegaImage, tempFile
from .forms import RegisterForm, SignInForm, TextForm, DecryptForm, MultipleDataForm, DeleteFileForm
from . import stega

def index(request):
    return render(request, 'main/index.html')

def about(request):
    title = 'About'
    return render(request, 'main/about.html', {'title': title})

# Deborah Venuti added login_required decorator
# Gene Ryasnianskiy added archive display and delete logic
@login_required(login_url='/signin')
def profile(request):
    title = 'Profile'

    #Get user's files
    archiveFiles = stegaImage.objects.all().filter(uploader = request.user)

    #Form for deleting archive items
    if (request.method == 'POST'):
        delete_file_form = DeleteFileForm(request.POST)

        #Delete each item and each file by ID
        for itemID in request.POST.getlist('delete'):
            objToDelete = stegaImage.objects.get(id=itemID)
            try:
                os.remove(os.path.join(MEDIA_ROOT, objToDelete.FinalImage.name))
            except:
                pass
            try:
                os.remove(os.path.join(MEDIA_ROOT, objToDelete.BaseImage.name))
            except:
                pass
            try:
                os.remove(os.path.join(MEDIA_ROOT, objToDelete.TarFile.name))
            except:
                pass
            objToDelete.delete()

    else:
        delete_file_form = DeleteFileForm()

    context = {
        'title': title,
        'archive': archiveFiles,
        'delete_file_form': delete_file_form,
        }

    return render(request, 'main/profile.html', context)

# Deborah Venuti added this
# Gene Ryasnianskiy image upload and processing
# Alex Sumner modified to accept multiple images and tar them
# Gene Ryasnaksiy moved documents display to archive in profile view
@login_required(login_url='/signin')
def encrypt(request):
    title = 'Encrypt'

    userObject = User.objects.get(username = request.user.username)
    text_invalid = False
    file_invalid = False

    # Handle file upload
    if request.method == 'POST':

        #create form objects
        multiple_data_form = MultipleDataForm(request.POST, request.FILES)
        text_form = TextForm(request.POST, request.FILES)


        #form for gathering files and inserting them into a carrier
        if multiple_data_form.is_valid():

            #grab the information from the submitted form
            output = ContentFile(bytes(0))
            carrier = multiple_data_form.cleaned_data['carrier']
            tFile = tarfile.open("Data.tar", 'w:gz')

            #temporarily store the files to facilitate taring them later
            for each in multiple_data_form.cleaned_data['Files']:
                newfile = tempFile(uploader=request.user)
                newfile.file.save(each.name, each)
                tFile.add(("./static" + newfile.file.url), arcname=each.name)
                os.remove(os.path.join(MEDIA_ROOT, newfile.file.name))
                newfile.delete()

            #close the tar file
            tFile.close()

            #open file opject to grab the tar file
            data = open('Data.tar', mode = 'r+b')
            datas = File(data)

            #insert the data into the carrier
            try:
                stega.inject_file(carrier, datas.file , output)
                #save the steganographed image to the users database
                newimage = stegaImage(uploader=request.user, processType='Encrypt File')
                newimage.FinalImage.save(carrier.name, output)
                newimage.BaseImage.save(carrier.name, carrier)
                newimage.TarFile.save(datas.name, datas.file)

                #close the file objects and delete the temp tar file
                datas.close()
                data.close()
                os.remove(data.name)
                
                #return to the page
                return HttpResponseRedirect(reverse('profile'))

            except stega.ByteOperationError as e:
                file_invalid = True


        #form for text insertion
        if text_form.is_valid():

            #grab information from the submitted form
            output = ContentFile(bytes(0))
            carrier = text_form.cleaned_data['carrier']
            text = text_form.cleaned_data['text']

            #inject the text into the image
            try:
                stega.inject_text(carrier, text , output)
                #save the steganographed image into the users database
                new = stegaImage(uploader=request.user, processType='Encrypt Text')
                new.FinalImage.save(carrier.name, output)
                new.BaseImage.save(carrier.name, carrier)
                
                #return to the page
                return HttpResponseRedirect(reverse('profile'))
            
            except stega.ByteOperationError as e:
                text_invalid = True

    else:
        #set defaults for when no data has been submitted
        multiple_data_form = MultipleDataForm()
        text_form = TextForm()

    #create list of information to send over the the .html file
    context = {
        'multiple_data_form': multiple_data_form,
        'text_form': text_form,
        'title': title,
        'text_invalid': text_invalid,
        'file_invalid': file_invalid,
        }

    #load the page
    return render(request, 'main/encrypt.html', context)


#Alexander Sumner - tab for decrypting images
@login_required(login_url='/signin')
def decrypt(request):
    title = 'Decrypt'

    #gather user information
    userObject = User.objects.get(username = request.user.username)
    message = ''

    if (request.method == 'POST'):

        decrypt_form = DecryptForm(request.POST, request.FILES)

        if decrypt_form.is_valid():
            #form for extracting text
            if decrypt_form.cleaned_data['choice'] == decrypt_form.TEXT :
                #initialize data and grab the encrypted message
                carrier = decrypt_form.cleaned_data['carrier']
                message = stega.extract_text(carrier)
                
                #create a text file to save the message
                textfile = open("Decrypted_Text.txt", "w")
                textfile.write(message)
                textfile.close()
                data = open("Decrypted_Text.txt", mode = 'r+b')
                datas = File(data)
                
                #create a database entry for the decrypted text
                new = stegaImage(uploader=request.user, processType='Decrypt Text')
                new.BaseImage.save(carrier.name, carrier)
                new.TarFile.save(datas.name, datas.file)

                #close and remove the temp txt file
                datas.close()
                data.close()
                os.remove(data.name)

            #form for extracting files
            elif decrypt_form.cleaned_data['choice'] == decrypt_form.FILE :
                output = ContentFile(bytes(0))
                carrier = decrypt_form.cleaned_data['carrier']

                #extracting is currently in development
                stega.extract_file(carrier, output)

                #save the extracted file to the users database
                new = stegaImage(uploader=request.user, processType='Decrypt File')
                new.BaseImage.save(carrier.name, carrier)
                new.TarFile.save('Data.tar', output)

                return HttpResponseRedirect(reverse('profile'))


    else:
        decrypt_form = DecryptForm()


    context = {
        'decrypt_form': decrypt_form,
        'title': title,
        'message': message,
        }

    return render(request, 'main/decrypt.html', context)



# Deborah Venuti added return of invalid indicator for sign in attempt of non-existing account
def signin(request):
    title = 'Sign In'

    if (request.method == 'POST'):
        form = SignInForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data
            userName = formData['email']
            userPassword = formData['password']

            user = authenticate(username=userName, password=userPassword)
            print(user)
            if (user is not None):
                login(request,user)
                return HttpResponseRedirect('/profile')
            else:
                return render(request, 'main/signin.html', {'form':form, 'invalid': True})
        else:
             return render(request, 'main/signin.html', {'form':form, 'invalid': True})

    else:
        form = SignInForm()
    return render(request, 'main/signin.html', {'form': form, 'title': title})

def register(request):
    title = 'Register'

    if (request.method == 'POST'):
        form = RegisterForm(request.POST)
        if form.is_valid():
            formData = form.cleaned_data

            try:
                user = User.objects.get(username=formData['email'])
                if (user is not None):
                    return render(request, 'main/register.html', {'form':form, 'invalid': True})

            except User.DoesNotExist:
                user = User.objects.create_user(formData['email'], formData['email'], formData['password'], first_name=formData['first_name'], last_name=formData['last_name'])
                user.save()

            return HttpResponseRedirect('/signin')

    else:
        form = RegisterForm()
    return render(request, 'main/register.html', {'form': form, 'title':title})
