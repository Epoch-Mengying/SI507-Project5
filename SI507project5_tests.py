import unittest
from SI507project5_code import *

class Tumplr_API_Test(unittest.TestCase):
    def setUp(self):
        self.myblogfile = open("mengyingzhangworld_text.csv")
        self.myquotefile = open("mengyingzhangworld_quote.csv")
        self.dreamerfile = open("logicaldreamer_quote.csv")
        self.cachefile = open("cache_contents.json")
        self.credsfile = open("creds.json")
    
    def test_csvfile_exist(self):
        self.assertTrue(self.myblogfile.read())
        self.assertTrue(self.myquotefile.read())
        self.assertTrue(self.dreamerfile.read())
        
    def test_quote_content(self):
        # This test may fail due to change in the blog site
        # Test the contents by checking the column names and first(second) row element
        self.assertTrue(self.myquotefile.readline(), "Post_Type, Note_Count, Quote_Content, Post_Source_URL")
        self.assertTrue(self.myquotefile.readline(), "quote, 0, Be the person who you want to meet., https://mengyingzhangworld.tumblr.com/post/167215491794/be-the-person-who-you-want-to-meet")  
        self.assertTrue(self.dreamerfile.readline(), "Post_Type, Note_Count, Quote_Content, Post_Source_URL")
        self.dreamerfile.readline()
        self.assertTrue(self.dreamerfile.readline(), "quote, 423, How could I leave you when I love you so?, https://logicaldreamer.tumblr.com/post/167019829229/how-could-i-leave-you-when-i-love-you-so")
        
    def test_cache_file(self):
        self.assertTrue(self.cachefile.read())
        
    def test_creds_file(self):
        self.assertTrue(self.credsfile.read())  
         
    def test_text_content(self):
        # This test may fail due to change in the blog site
        self.assertTrue(self.myblogfile.readline(), "Post_Type, Note_Count, Title, Content, Source_URL")
        self.assertTrue(self.myquotefile.readline(), "text, 0, OAuth1, <p>I’m doing a project on Tumblr API. Who wants to be my target!</p>, https://mengyingzhangworld.tumblr.com/post/167323822104/oauth1")
                 
    def tearDown(self):
        self.myblogfile.close()
        self.myquotefile.close()
        self.dreamerfile.close()
        self.cachefile.close()
        self.credsfile.close()
  


if __name__ == '__main__':
    unittest.main(verbosity=2)


