import os
import pandas as pd
from functools import reduce
from django.shortcuts import render, redirect
from datetime import datetime
from validate_email import validate_email
import pyrebase
import firebase_admin
from firebase_admin import credentials
#from firebase_admin import auth
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import logout
from django.core.files.storage import default_storage
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
from datetime import datetime
import smtplib, ssl

# Create your views here.

config = {
  "apiKey": "AIzaSyDIDHyLXDArAIIT29h0IwE7ipWy5pn2ZcQ",
  "authDomain": "e-doctors-ffa02.firebaseapp.com",
  "databaseURL": "https://e-doctors-ffa02-default-rtdb.firebaseio.com",
  "projectId": "e-doctors-ffa02",
  "storageBucket": "e-doctors-ffa02.appspot.com",
  "messagingSenderId": "9903158176",
  "appId": "1:9903158176:web:f521117415e536e3382ac5",
};

firebase = pyrebase.initialize_app(config)
pyre_auth = firebase.auth()
database = firebase.database()
storage = firebase.storage()
cred = credentials.Certificate("e-doctors-ffa02-firebase-adminsdk-enrb6-ad5cf88c0c.json")
#firebase_admin.initialize_app(cred)
login_user = None


# Functions
def load_doctor_data(request, id=""):
    if id == "":
         id = request.session['uid']

    doctor = database.child("Doctors").order_by_child("doctor_id").equal_to(id).get()
    about_me = ""
    speciality = ""
    username = ""
    rating = 0
    email = ""
    clinic_name = ""
    clinic_address = ""
    clinic_location = ""
    clinic_visit_hourly_rate = 0
    home_visit_hourly_rate = 0
    profile_pic_url = ""
    cert_url = ""

    for d in doctor.each():
        about_me = d.val()['about_me']
        speciality = d.val()['speciality']
        username = d.val()['username']
        rating = d.val()['ratings']
        email = d.val()['email']
        clinic_name = d.val()['clinic_name']
        clinic_address = d.val()['clinic_address']
        clinic_location = d.val()['clinic_location']
        clinic_visit_hourly_rate = d.val()['clinic_visit_hourly_rate']
        home_visit_hourly_rate = d.val()['home_visit_hourly_rate']
        profile_pic_url = d.val()['profile_pic_url']
        cert_url = d.val()['cert_url']

    context = {
        'user_id': request.session['uid'],
        'about_me': about_me,
        'speciality': speciality,
        'username': username,
        'rating': rating,
        'email': email,
        'clinic_name': clinic_name,
        'clinic_address': clinic_address,
        'clinic_location' : clinic_location,
        'clinic_visit_hourly_rate' : clinic_visit_hourly_rate,
        'home_visit_hourly_rate' : home_visit_hourly_rate,
        'profile_pic_url' : profile_pic_url,
        'cert_url' : cert_url,
    }

    return context



def load_patient_data(request, id = ""):
    if id == "":
         id = request.session['uid']

    patient = database.child("Patients").order_by_child("patient_id").equal_to(id).get()
    about_me = ""
    speciality = ""
    username = ""
    rating = 0
    email = ""
    clinic_name = ""
    clinic_address = ""
    clinic_location = ""
    clinic_visit_hourly_rate = 0
    home_visit_hourly_rate = 0
    profile_pic_url = ""
    cert_url = ""

    for p in patient.each():
        username = p.val()['username']
        email = p.val()['email']
        password = p.val()['password']
        gender = p.val()['gender']
        blood_type = p.val()['blood_type']
        height_cm = p.val()['height_cm']
        weight_kg = p.val()['weight_kg']
        dob = p.val()['dob']
        medical_history = p.val()['medical_history']
        profile_pic_url = p.val()['profile_pic_url']

    context = {
        'patient_id': request.session['uid'],
        'username': username,
        'email': email,
        'password': password,
        'gender' : gender,
        'blood_type' : blood_type,
        'height_cm' : height_cm,
        'weight_kg' : weight_kg,
        'dob' : dob,
        'medical_history' : medical_history,
        'profile_pic_url' : profile_pic_url
    }

    return context



def get_username(uid, user_type):
    db_node = ""
    id_name = ""
    username = ""

    if user_type == "doctor":
        db_node = "Doctors"
        id_name = "doctor_id"
    else:
        db_node = "Patients"
        id_name = "patient_id"

    attrs = database.child(db_node).order_by_child(id_name).equal_to(uid).get()

    for attr in attrs.each():
        username = attr.val()['username']

    print("Username: ", username)
    return username


# Views
def logout_user(request):
    logout(request)
    # print(request.session['uid'])
    return redirect("home")


def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            login_user = pyre_auth.sign_in_with_email_and_password(email, password)
            print(login_user)
            session_id = login_user['localId']
            request.session['uid'] = str(session_id)
            request.session['email'] = email
            request.session['password'] = password


            if database.child('Doctors').child(session_id).shallow().get().val():
                request.session['user_type'] = 'doctor'
                request.session['username'] = get_username(request.session['uid'], request.session['user_type'])
                return redirect("doctor_profile")

            elif database.child('Patients').child(session_id).shallow().get().val():
                request.session['user_type'] = 'patient'
                request.session['username'] = get_username(request.session['uid'], request.session['user_type'])
                print("request.session['username']: ", request.session['username'])
                return redirect("home")

            else:
                print("USER TYPE UNCLASSIFIED. PLEASE CHECK YOUR FIREBASE")
                return redirect("home")
        except:
            messages.error(request, 'Invalid email or password.')

    context = {
    'navbar_class' : 'static-top',
    'session' : request.session,
    }
    return render(request, 'base/login.html', context)




def sign_up(request):
    if request.method == 'POST':
        try:
            now = datetime.now()
            reg_date = now.strftime("%d/%m/%Y %H:%M:%S")
            email = request.POST.get('email')
            password = request.POST.get('password')
            valid = validate_email(email)

            if valid:
                user = pyre_auth.create_user_with_email_and_password(email, password)
                login_user = pyre_auth.sign_in_with_email_and_password(email, password)
                session_id = login_user['localId']
                request.session['uid'] = str(session_id)
                request.session['email'] = email
                request.session['password'] = password

                if 'patient-sign-up' in request.POST:
                    u = {
                        'patient_id': user['localId'],
                        'username': "",
                        'email': email,
                        'password': password,
                        'reg_date': reg_date,
                        'gender' : "",
                        'blood_type' : "",
                        'height_cm' : "",
                        'weight_kg' : "",
                        'dob' : "",
                        'medical_history' : "",
                        'profile_pic_url' : "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/2048px-No_image_available.svg.png",
                    }

                    database.child('Patients').child(user['localId']).set(u)
                    request.session['user_type'] = 'patient'
                    request.session['username'] = get_username(request.session['uid'], request.session['user_type'])
                    return redirect("edit_patient_profile")

                elif 'doctor-sign-up' in request.POST:
                    u = {
                        'doctor_id': user['localId'],
                        'username': "",
                        'email': email,
                        'password': password,
                        'reg_date': reg_date,
                        'speciality' : "",
                        'clinic_name' : "",
                        'clinic_address' : "",
                        'clinic_location' : "",
                        'clinic_visit_hourly_rate' : 0,
                        'home_visit_hourly_rate' : 0,
                        'about_me' : "",
                        'available_clinic_visit_timestamp' : [],
                        'available_home_visit_timestamp' : [],
                        'ratings' : 0,
                        'number_of_ratings' : 0,
                        'profile_pic_url' : "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/2048px-No_image_available.svg.png",
                        'cert_url' : '',
                    }

                    database.child('Doctors').child(user['localId']).set(u)
                    request.session['user_type'] = 'doctor'
                    request.session['username'] = get_username(request.session['uid'], request.session['user_type'])
                    return redirect("edit_doctor_profile")
            else:
                messages.error(request, 'Invalid email.')
        except:
            messages.error(request, 'Account already exist. Please login.')

    context = {
        'session' : request.session,
        'navbar_class' : 'static-top'
    }

    return render(request, 'base/sign-up.html', context)



def blogs(request):

    return render(request, 'base/index_blog.html')

def omicron(request):
    
    return render(request, 'base/omicron.html')

def heart(request):

    return render(request, 'base/heart-attacks.html')

def healthy(request):

    return render(request, 'base/healthy-food.html')


def view_doctor_profile(request, doctor_id):
    if 'btnRate' in request.POST:
        patient_id = request.session['uid']
        review = request.POST.get('review')
        rating = request.POST.get('rating')
        timestamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

        rate = {
            'doctor_id' : doctor_id,
            'patient_id' : patient_id,
            'rating' : rating,
            'review' : review,
            'timestamp' : timestamp,
        }

        r = database.child('Reviews').push(rate)
        database.child("Reviews").child(r['name']).update({"review_id": r['name']})

    emails = []
    df_reviews = pd.DataFrame()
    if database.child('Reviews').shallow().get().val():
        reviews = database.child("Reviews").order_by_child("doctor_id").equal_to(doctor_id).get()
        review_dict = []
        for r in reviews.each():
            review_dict.append(r.val())

            patient = database.child("Patients").order_by_child("patient_id").equal_to(r.val()['patient_id']).get()

            for p in patient.each():
                emails.append(p.val()['email'])

        df_reviews = df_reviews.append(review_dict, ignore_index=True)
        df_reviews['patient_email'] = emails


    context = load_doctor_data(request, doctor_id)
    context['session'] = request.session
    context['navbar_class'] = 'static-top'
    context['df_reviews'] = df_reviews
    return render(request, 'base/view-doctor-profile.html', context)



def doctor_profile(request):
    if 'btnAddMore' in request.POST:
        return redirect("edit_doctor_profile")

    emails = []
    df_reviews = pd.DataFrame()
    if database.child('Reviews').shallow().get().val():
        reviews = database.child("Reviews").order_by_child("doctor_id").equal_to(doctor_id).get()
        review_dict = []
        for r in reviews.each():
            review_dict.append(r.val())

            patient = database.child("Patients").order_by_child("patient_id").equal_to(r.val()['patient_id']).get()

            for p in patient.each():
                emails.append(p.val()['email'])

        df_reviews = df_reviews.append(review_dict, ignore_index=True)
        df_reviews['patient_email'] = emails

    context = load_doctor_data(request)
    print("context['profile_pic_url']:", context['profile_pic_url'])
    context['session'] = request.session
    context['navbar_class'] = 'static-top'
    return render(request, 'base/doctor-profile.html', context)



def edit_doctor_profile(request):
    if 'btnUpdate' in request.POST:
        full_name = request.POST.get('fullName')
        speciality = request.POST.get('speciality')
        about = request.POST.get('about')
        clinic_name = request.POST.get('clinic_name')
        clinic_address = request.POST.get('clinic_address')
        clinic_location = request.POST.get('clinic_location')
        clinic_visit_hourly_rate = request.POST.get('clinic_visit_hourly_rate')
        home_visit_hourly_rate = request.POST.get('home_visit_hourly_rate')
        password = request.POST.get('password')
        image = request.FILES['profile_pic']

        print("request.session: ", request.session)
        print("request.session['password']: ",  request.session['password'])
        print("password: ",  password)
        if request.session['password'] == password:
            url = ""
            image_save = default_storage.save(image.name, image)
            storage.child("doctors/" + request.session['uid'] + "profile_pic.jpg").put(image.name, request.session['uid'])
            url = storage.child("doctors/" + request.session['uid'] + "profile_pic.jpg").get_url(request.session['uid'])


            u = {
                'username' : full_name,
                'speciality' : speciality,
                'about_me' : about,
                'clinic_name' : clinic_name,
                'clinic_address' : clinic_address,
                'clinic_location' : clinic_location,
                'clinic_visit_hourly_rate' : clinic_visit_hourly_rate,
                'home_visit_hourly_rate' : home_visit_hourly_rate,
                'profile_pic_url' : url
            }

            database.child("Doctors").child(request.session['uid']).update(u)
            delete = default_storage.delete(image.name)
            return redirect("doctor_profile")
        else:
            messages.error(request, 'Invalid Password.')

    context = load_doctor_data(request)
    context['session'] = request.session
    context['navbar_class'] = 'static-top'
    return render(request, 'base/edit-doctor-profile.html', context)



def patient_profile(request):
    if 'btnAddMore' in request.POST:
        return redirect("edit_patient_profile")
    context = load_patient_data(request)
    context['session'] = request.session
    context['navbar_class'] = 'static-top'
    return render(request, 'base/patient-profile.html', context)


def edit_patient_profile(request):
    if 'btnUpdate' in request.POST:
        full_name = request.POST.get('fullName')
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        blood_type = request.POST.get('blood_type')
        height_cm = request.POST.get('height_cm')
        weight_kg = request.POST.get('weight_kg')
        medical_history = request.POST.get('medical_history')
        password = request.POST.get('password')
        image = request.FILES['profile_pic']

        print("request.session: ", request.session)
        print("request.session['password']: ",  request.session['password'])
        print("password: ",  password)
        if request.session['password'] == password:
            url = ""
            image_save = default_storage.save(image.name, image)
            storage.child("patients/" + request.session['uid'] + "profile_pic.jpg").put(image.name, request.session['uid'])
            url = storage.child("patients/" + request.session['uid'] + "profile_pic.jpg").get_url(request.session['uid'])


            u = {
                'username' : full_name,
                'dob' : dob,
                'gender' : gender,
                'blood_type' : blood_type,
                'height_cm' : height_cm,
                'weight_kg' : weight_kg,
                'medical_history' : medical_history,
                'profile_pic_url' : url
            }

            database.child("Patients").child(request.session['uid']).update(u)
            delete = default_storage.delete(image.name)
            return redirect("patient_profile")
        else:
            messages.error(request, 'Invalid Password.')

    context = load_patient_data(request)
    context['session'] = request.session
    context['navbar_class'] = 'static-top'
    return render(request, 'base/edit-patient-profile.html', context)


def home(request):
    # Find a Doctor Section
    #Display all the list of clinics
    clinic_no = database.child('Doctors').shallow().get().val()
    list_clinic = []
    for i in clinic_no:
        list_clinic.append(i)
        list_clinic.sort(reverse=False)

    print('list_clinic: ', list_clinic)

    filter_clinic_id=[]
    filter_image = []
    filter_doctor = []
    filter_clinic = []
    filter_location = []
    filter_speciality = []

    for i in list_clinic:
        filter_clinic_i = database.child('Doctors').child(i).child('doctor_id').get().val()
        filter_clinic_id.append(filter_clinic_i)
    # print(filter_location)

    for i in list_clinic:
        filter_imag = database.child('Doctors').child(i).child('profile_pic_url').get().val()
        filter_image.append(filter_imag)
    #print(filter_image)

    for i in list_clinic:
        filter_docto = database.child('Doctors').child(i).child('username').get().val()
        filter_doctor.append(filter_docto)
    # print(filter_doctor)

    for i in list_clinic:
        filter_clini = database.child('Doctors').child(i).child('clinic_name').get().val()
        filter_clinic.append(filter_clini)
    # print(filter_clinic)

    for i in list_clinic:
        filter_specialit = database.child('Doctors').child(i).child('speciality').get().val()
        filter_speciality.append(filter_specialit)
    # print(filter_speciality)

    for i in list_clinic:
        filter_locatio = database.child('Doctors').child(i).child('clinic_location').get().val()
        filter_location.append(filter_locatio)
    # print(filter_location)

    cert_url = []
    for i in list_clinic:
        cert_ur = database.child('Doctors').child(i).child('cert_url').get().val()
        cert_url.append(cert_ur)

    df_combined = None

    if 'search-filter-button' in request.GET and 'csrfmiddlewaretoken' in request.GET:
        clinic_list = None
        search_clinic_list = list(zip(filter_clinic_id, filter_image, filter_doctor, filter_clinic, filter_speciality, filter_location))

        df_unfiltered = pd.DataFrame(search_clinic_list, columns= ['filter_clinic_id', 'filter_image', 'filter_doctor', 'filter_clinic', 'filter_speciality', 'filter_location'] )

        print('df_unfiltered: ', df_unfiltered)

        df_filtered_clinic = pd.DataFrame()
        df_filtered_location = pd.DataFrame()
        df_filtered_speciality = pd.DataFrame()

        filter_dataframe_list = []

        search_clinic = request.GET.get('search-clinic')
        search_location = request.GET.get('filter-location')
        search_speciality = request.GET.get('filter-speciality')

        df_unfiltered['clinic_name_lower'] = df_unfiltered['filter_clinic'].str.lower()
        df_unfiltered['speciality_lower'] = df_unfiltered['filter_speciality'].str.lower()
        df_unfiltered['location_lower'] = df_unfiltered['filter_location'].str.lower()

        print(df_unfiltered)
        print()

        df_filtered_clinic = df_unfiltered[df_unfiltered["clinic_name_lower"].str.contains(search_clinic.lower())]
        df_filtered_speciality = df_unfiltered[df_unfiltered["speciality_lower"].str.contains(search_speciality.lower())]
        df_filtered_location = df_unfiltered[df_unfiltered["location_lower"].str.contains(search_location.lower())]

        if len(df_filtered_clinic) > 0:
            filter_dataframe_list.append(df_filtered_clinic)
        if len(df_filtered_location) > 0 :
            filter_dataframe_list.append(df_filtered_location)
        if len(df_filtered_speciality) > 0 :
            filter_dataframe_list.append(df_filtered_speciality)

        if (len(df_filtered_clinic) == 0 and (not search_clinic == "")) or (len(df_filtered_location) == 0 and (not search_location == "")) or (len(df_filtered_speciality) == 0 and (not search_speciality == "")):
            df_combined = None
            print("No result found...")
        else:
            df_combined = reduce(lambda left, right:
                                pd.merge(left , right,
                                        on = ['filter_clinic_id', 'filter_image', 'filter_doctor', 'filter_clinic', 'filter_speciality', 'filter_location', "clinic_name_lower", "location_lower", 'speciality_lower']),

                                filter_dataframe_list)

            print("Filtered Result:", df_combined)
    else:
        clinic_list = zip(filter_clinic_id, filter_image, filter_doctor, filter_clinic, filter_speciality, filter_location)

    # Appointment
    doc_option = filter_doctor

    # Count section
    count_doctor = len(database.child('Doctors').get().val())
    count_clinic_list = list(zip(filter_clinic_id, filter_image, filter_doctor, filter_clinic, filter_speciality, filter_location,cert_url))
    df_count = pd.DataFrame(count_clinic_list, columns= ['filter_clinic_id', 'filter_image', 'filter_doctor', 'filter_clinic', 'filter_speciality', 'filter_location', 'cert_url'] )
    # count_speciality = df_count[df_count.columns[4]].count()
    count_speciality = len(df_count["filter_speciality"].unique())
    count_location = len(df_count["filter_location"].unique())
    count_cert = len(df_count["cert_url"].unique())

    # Frequently Asked Questions Section
    faquestion_no = database.child('FAQ').shallow().get().val()
    list_faquestion = []
    for i in faquestion_no:
        list_faquestion.append(i)
        list_faquestion.sort(reverse=False)
    # print(list_faquestion)

    faquestion =[]
    faqanswer =[]

    for i in list_faquestion:
        faquestio = database.child('FAQ').child(i).child('question').get().val()
        faquestion.append(faquestio)
    # print(faquestion)

    for i in list_faquestion:
        faqanswe = database.child('FAQ').child(i).child('answer').get().val()
        faqanswer.append(faqanswe)
    # print(faqanswer)

    faq_list = zip(faquestion, faqanswer)


    if request.POST.get("btnAppointment") == 'btnAppointment':

        patient_name = request.POST.get('name')
        patient_email = request.POST.get('email')
        phone_number = request.POST.get('phone')
        date_appointment = request.POST.get('date')
        doctor_name = request.POST.get('doctor')
        msg = request.POST.get('message')

        website_email = 'edoctors.official@gmail.com'
        email_password = 'kxfdudzhenyzpzcs'
        subject = 'Patient: ' + patient_name
        message = 'Dear ' + doctor_name + ',\n\nKindly accept or decline patient appointment shown below.\n\nPatient Name: ' + patient_name + '\n\nPatient Email: ' + patient_email + '\n\nPatient Contact: ' + phone_number + '\n\nAppointment Date: ' + date_appointment + '\n\nMessage: ' + msg + '\n\n'


        # send_mail(subject, message, web_email, ['0129398@kdu-online.com'])           
        emails = ['0129398@kdu-online.com']
        emails = [e.replace(' ', '') for e in emails]

        sent_from = website_email
        to = emails
        body = message

        email_text = 'Subject: {}\n\n{}'.format(subject, body)

        try:
            smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            smtp_server.ehlo()
            smtp_server.login(website_email, email_password)
            smtp_server.sendmail(sent_from, to, email_text)
            smtp_server.close()
            print("Success")
        except Exception as ex:
            print("error")


    # if request.POST.get("btn_appointment") == 'btn_appointment':
    #     doctor_id = request.POST.get('doctor_id')
    #     return redirect("edit_doctor_profile", doctor_id)

    context = {
    'clinic_list': clinic_list,
    'df_combined':df_combined,
    'faq_list': faq_list,
    'count_doctor': count_doctor,
    'count_speciality': count_speciality,
    'count_location' : count_location,
    'count_cert' : count_cert,
    'navbar_class' : 'fixed-top',
    'session' : request.session,
    'doc_option' : doc_option,
    }

    return render(request, 'base/index.html', context)
