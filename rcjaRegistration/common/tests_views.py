from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.test import Client




class AuthViewTests(TestCase):

    username = 'newuser'
    password = 'password123'


    def testSignupByUrl(self):
        response = self.client.get('/accounts/signup')
        self.assertEqual(response.status_code, 200)

    def testSignupByName(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)

    def testSignupUsesCorrectTemplate(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/signup.html')

    def testUserValidSignup(self):
        prevUsers = get_user_model().objects.all().count()

        payloadData = {'username':self.username,'password1':self.password,'password2':self.password}
        response = self.client.post(path=reverse('signup'),data = payloadData)
        self.assertEqual(response.status_code,302) #ensure user is redirected on signup
        self.assertEqual(get_user_model().objects.all().count(), prevUsers + 1)
        self.assertEqual(get_user_model().objects.all()
                         [0].username, self.username) #this checks the user created has the right username
                                                    #note that this works because transactions aren't saved in django tests

    def testUserInvalidSignup(self):
        payloadData = {'username':self.username,'password1':self.password,'password2':'onetwothree'}
        response = self.client.post(path=reverse('signup'),data = payloadData)
        self.assertEqual(response.status_code,200) #ensure user is not redirected
        self.assertEqual(get_user_model().objects.all().count(), 0)
    
    def testUserExistingSignup(self):
        payloadData = {'username':self.username,'password1':self.password,'password2':self.password}
        self.client.post(path=reverse('signup'),data = payloadData)
        response = self.client.post(path=reverse('signup'), data = payloadData)
        self.assertEqual(response.status_code,200) #ensure failed signup
        self.assertIn(b'A user with that username already exists.',response.content)


    def testLoginByUrl(self):
        response = self.client.get('/accounts/login')
        self.assertEqual(response.status_code, 200)

    def testLoginByName(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def testLoginUsesCorrectTemplate(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')


    def testUserCreatedLogsIn(self):
        payloadData = {'username':self.username,'password1':self.password,'password2':self.password}
        self.client.post(path=reverse('signup'),data = payloadData)
        loginPayload = {'username':self.username,'password':self.password}
        response = self.client.post(path=reverse('login'),data = loginPayload)
        self.assertEqual(response.status_code,302) #ensure a successful login works and redirects