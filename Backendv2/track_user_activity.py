'''
This script will handle user accounts and user activity.

We will create accounts for everyone in the website, 
and save all their activity onto our MongoDB database
so that they can fetch their generated content upon visiting
the website again.
'''

class UserSession():
    def __init__(self, user, password):
        self.user = user
        # Initialize or validate user login here


    def populate_website_for_user(self):
        pass


    def save_generated_article_to_cache(self, article):
        pass

