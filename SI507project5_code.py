import requests_oauthlib
import webbrowser
import json
import pandas as pd
import csv
import secret_data # need properly formatted file, see example
from datetime import datetime

##### CACHING SETUP #####
#--------------------------------------------------
# Caching constants
#--------------------------------------------------
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
DEBUG= True
CACHE_FNAME = "cache_contents.json" # a cache file to save the returned data
CREDS_CACHE_FNAME = "creds.json" # a cache file to save the credentials, ie, all the tokens

#--------------------------------------------------
# Load cache files: data and credentials
#--------------------------------------------------
# Load data cache
try:
    with open(CACHE_FNAME,'r') as cache_file:
        cache_json = cache_file.read()
        CACHE_DICTION = json.loads(cache_json)
except:
    CACHE_DICTION = {}
    
# Load credential cache
try:
    with open(CREDS_CACHE_FNAME,'r') as creds_file:
        creds_json = creds_file.read()
        CREDS_DICTION = json.loads(creds_json)
except:
    CREDS_DICTION = {}

#---------------------------------------------------------------------------
# Cache functions: check if cache has expired, get/set data from cache
#---------------------------------------------------------------------------
def has_cache_expired(timestamp_str, expire_in_days):
    """Check if cache timestamp is over expire_in_days old"""
    # current time
    now = datetime.now()
    
    # convert timestramp_str, a formatted string to a datetime object
    cache_timestramp = datetime.strptime(timestamp_str, DATETIME_FORMAT)
    
    # How long since the cache created from now?
    diff = now - cache_timestramp
    diff_in_days = diff.days
    
    # determine if the cache has expired or not
    if diff_in_days > expire_in_days:
        return True
    else:
        return False

def get_from_cache(identifier, cache_dictionary):
    """If unique identifier exists in specified cache dictionary and has not expired, return the data associated with it from the request, else return None"""
    identifier = identifier.upper() # saved all identifiers in upper case
    # find the identifier in the cache_dictionary
    if identifier in cache_dictionary:
        data_assoc_dict = cache_dictionary[identifier]
        if has_cache_expired(data_assoc_dict['timestamp'], data_assoc_dict['expire_in_days']):
            if DEBUG:
                print ("Cache has expired for {}".format(identifier))
            # if expired, delete the corresponding cache and return None
            del cache_dictionary[identifier]
            data = None
        else:
            data = data_assoc_dict['values']
    else:
        data = None
    return data
    
def set_in_data_cache(identifier, data, expire_in_days):
    """Add identifier and its associated values (literal data) to the data cache dictionary, and save the whole dictionary to a file as json"""
    # save in cache dictionary
    identifier = identifier.upper()
    CACHE_DICTION[identifier] = {
        "values": data,
        'timestamp': datetime.now().strftime(DATETIME_FORMAT), # convert datetime object to string
        'expire_in_days': expire_in_days
    }
    
    # write on cache file
    with open(CACHE_FNAME, 'w') as cache_file:
        cache_json = json.dumps(CACHE_DICTION)
        cache_file.write(cache_json)
        
def set_in_creds_cache(identifier, data, expire_in_days):
    """Add identifier and its associated values (literal data) to the credentials cache dictionary, and save the whole dictionary to a file as json"""
    identifier = identifier.upper()
    CREDS_DICTION[identifier] = {
        'values': data,
        'timestamp': datetime.now().strftime(DATETIME_FORMAT), # convert datetime object to string
        'expire_in_days': expire_in_days
    }
    
    # write on cache file
    with open(CREDS_CACHE_FNAME, 'w') as creds_file:
        creds_json = json.dumps(CREDS_DICTION)
        creds_file.write(creds_json)  


##### OAuth1 API #######        
#---------------------------------------------
# Tumblr API Info
#---------------------------------------------  
CLIENT_KEY = secret_data.client_key # what Tumblr calls Consumer Key
CLIENT_SECRET = secret_data.client_secret # What Tumblr calls Consumer Secret

### Specific to API URLs, not private
REQUEST_TOKEN_URL = "https://www.tumblr.com/oauth/request_token"
BASE_AUTH_URL = "https://www.tumblr.com/oauth/authorize" # + param{ClientID+RedirectURL+Scope}
ACCESS_TOKEN_URL = "https://www.tumblr.com/oauth/access_token"


#-----------------------------------------------------------------------------------------------
# Get tokens: client key, client secret, new oauth_token, new oauth_token_secret, oauth_verifier
# Tokens are used for creating a new session that uses tokens as credentials
#-----------------------------------------------------------------------------------------------
def get_tokens(client_key = CLIENT_KEY, client_secret = CLIENT_SECRET, request_token_url = REQUEST_TOKEN_URL, base_authorization_url = BASE_AUTH_URL, access_token_url = ACCESS_TOKEN_URL, verifier_auto = False):
    # step 1: Create a session: client_key and client_secret
    oauth_inst = requests_oauthlib.OAuth1Session(client_key, client_secret=client_secret)
    
    # step 2: Use request_token_url to get oauth token, oauth token secret from Tumblr
    fetch_response = oauth_inst.fetch_request_token(request_token_url)
    
    # step 3: Get oauth token, oauth token secret
    # Authorization URL: baseurl + client_key, client_secret, oauth token, oauth token secret(incorporated in the oauth instance)
    oauth_token = fetch_response['oauth_token']
    oauth_token_secret = fetch_response['oauth_token_secret']
    
    auth_url = oauth_inst.authorization_url(base_authorization_url)
    # step 4: Open the auth url in browser:
    webbrowser.open(auth_url) # For user to interact with & approve access of this app -- this script. This will redirect to another page with verifier
    
    # step 5: Get verification tokens
    if verifier_auto:
        verifier = input("Please input the verifier:  ")
    else:
        redirect_result = input("Paste the full redirect URL here:  ")
        oauth_resp = oauth_inst.parse_authorization_response(redirect_result) # returns a dictionary -- you may want to inspect that this works and edit accordingly
        verifier = oauth_resp['oauth_verifier']
        
    # step 6: Regenerate a new session with: client_key, client_secret, oauth token, oauth_token_secret, oauth_verifier
    oauth_inst = requests_oauthlib.OAuth1Session(client_key, client_secret=client_secret, resource_owner_key=oauth_token, resource_owner_secret=oauth_token_secret, verifier=verifier)
    
    # step 7: Get Access Token from the new session
    access_token = oauth_inst.fetch_access_token(access_token_url) # returns a dictionary
    
    # step 8: Use access_token to get a new oauth_token and oauth_token_secret
    oauth_token, oauth_token_secret = access_token.get('oauth_token'), access_token.get('oauth_token_secret') 
    
    return client_key, client_secret, oauth_token, oauth_token_secret, verifier

    
# If not in cache, call get_tokens() to fetch credentials/tokens, otherwise return from cache
def get_tokens_from_service(identifier, expire_in_days=3):
    creds_data = get_from_cache(identifier, CREDS_DICTION)
    if creds_data:
        if DEBUG:
            print("Loading credential data from cache...\n")
    else:
        if DEBUG:
            print("Fetching fresh credentials...")
            print("Prepare to log in via browser.\n")
        creds_data = get_tokens()
        set_in_creds_cache(identifier, creds_data, expire_in_days=expire_in_days)
        
    return creds_data


#-----------------------------------------------------------------------------------------------
# Get data from API using cached tokens
#-----------------------------------------------------------------------------------------------
def create_request_identifier(url, params_diction):
    sorted_params = sorted(params_diction.items(),key=lambda x:x[0])
    params_str = "_".join([str(e) for l in sorted_params for e in l]) # Make the list of tuples into a flat list using a complex list comprehension
    total_ident = url + "?" + params_str
    return total_ident.upper() # Creating the identifier

# step 9: Create a new session using (cached) credentials/tokens to get data from API
def get_data_from_api(request_url, identifier, params_diction, expire_in_days = 3):
    """Check in cache, if not found, load data, save in cache and then return that data"""
    ident = create_request_identifier(request_url, params_diction)
    data = get_from_cache(ident, CACHE_DICTION)
    if data:
        if DEBUG:
            print("Loading data from cache: {}...\n".format(ident))
    else:
        if DEBUG:
            print("Fetching new data from {}".format(request_url))
            
        # Get credentials/tokens
        client_key, client_secret, oauth_token, oauth_token_secret, verifier = get_tokens_from_service(identifier)
         
        # Make a new session to retrieve data
        oauth_inst = requests_oauthlib.OAuth1Session(client_key, client_secret=client_secret,resource_owner_key=oauth_token,resource_owner_secret=oauth_token_secret)
        # Call the get method on oauth instance
        # Work of encoding and "signing" the request happens behind the sences, thanks to the OAuth1Session instance in oauth_inst
        resp = oauth_inst.get(request_url,params=params_diction)
        # Get the string data and set it in the cache for next time
        data_str = resp.text
        data = json.loads(data_str)
        set_in_data_cache(ident, data, expire_in_days)
    return data  


##### Final Step: Get data from API and save it to csv files #######  
#-----------------------------------------------------------------------------------------------
# Helper functions for writing csv files
#-----------------------------------------------------------------------------------------------
## Helper Function for constructing search_url:
def get_likes_search_url(blog_identifier):
    return "https://api.tumblr.com/v2/blog/{id}/likes?api_key={key}".format(id= blog_identifier, key=CLIENT_KEY)

def get_posts_search_url(blog_identifier, type):
    return "https://api.tumblr.com/v2/blog/{id}/posts/{type}/?api_key={key}".format(id= blog_identifier, type = type, key=CLIENT_KEY)


## Helper Function for writing csv files for different types(either quote or text post) of post data:
def write_quote_files(posts_dict,filename):
    with open(filename,"w") as csvfile:
        csvfile.write("Post_Type,Note_Count,Quote_Content,Post_Source_URL\n")
        for post in posts_dict:
            csvfile.write('\"{}\",\"{}\",\"{}\",\"{}"\n'.format(post.get('type'), post.get('note_count'),post.get('text'), post.get('post_url')))

def write_text_files(posts_dict,filename):
    with open(filename,"w") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Post_Type", "Note_Count", "Title", "Content", "Source_URL"])
        for post in posts_dict:
            csv_writer.writerow([post.get('type'), post.get('note_count'), post.get('title'), post.get('body'), post.get('post_url')])
     
#-----------------------------------------------------------------------------------------------
# Use previous helper functions to write customerized csv files depending on types of blog.
#-----------------------------------------------------------------------------------------------            
            
## Helper Function for getting data from API and writing into customized csv files:
def write_user_file(blog_identifier, type = "quote", expire_in_days = 3):
    '''Create search url and get data(can only be quote or text) from API. Then customize the filename and write the data on file.'''
    # create search url
    search_url = get_posts_search_url(blog_identifier, type) 
    search_params = {}
    
    # invoke the function to get data from api
    result = get_data_from_api(request_url = search_url, identifier = "Tumblr", params_diction = search_params, expire_in_days = expire_in_days)
    
    # customize the filename to the {blog_identifier}_{type}.csv and write files
    type = type.lower()
    if type == "quote":
        filename = "{}_quote.csv".format(blog_identifier)
        write_quote_files(result.get('response')['posts'], filename)
        # some fun stuff: find and print the best liked(ie. highest note_count) quote in the blog
        df = pd.read_csv(filename)
        saved_column = df['Note_Count']
        Counts = [int(count) for count in saved_column]
        index = Counts.index(max(Counts))
        Best_Quote = df.iloc[index, 2]
        print ("-"*25)
        print("The best liked quote in {}'s blog is: {}". format(blog_identifier, str(Best_Quote)))
        print ("The quote received {} likes.".format(max(Counts)))
        print ("-"*25)
       
    elif type == "text":
        filename = "{}_text.csv".format(blog_identifier)
        write_text_files(result.get('response')['posts'], filename) 
    else:
        print("ERROR: Type not supported. Search type can only be \'quote\' or \'text\'.")
        ## sys.exit("Error message")  

#-----------------------------------------------------------------------------------------------


if __name__ == "__main__":
    if not CLIENT_KEY or not CLIENT_SECRET:
        print ("Please fill in Client key and Client secret in the secret_data.py file.")
        exit()
    if not REQUEST_TOKEN_URL or not BASE_AUTH_URL:
        print("You need to fill in this API's specific OAuth2 URLs in this file.")
        exit()
    
    ## Retrieve quote data from thegoodvybe and logicaldreamer; Retrieve text data from NASA 
    write_user_file("thegoodvybe", type = "quote")
    write_user_file("logicaldreamer", type = "quote")
    write_user_file("nasa", type = "text")
    write_user_file("mengyingzhangworld", type = "text") # My newly created blog
    write_user_file("mengyingzhangworld", type = "quote") # My newly created blog 
    
    if DEBUG: 
        print("Writing files completed.")
        
# The END 
##############################################################################################
############################################################################################## 
#-----------------------------------------------------------------------------------------------
# This line below is only For Helping programmers to do individual testing
    
    # Set request URL and params_diction
    # Tumblr_search_url = "https://api.tumblr.com/v2/blog/thegoodvybe/likes"
#     Tumblr_search_params = {"api_key": "gdzo9C2PN4z0ulfot6Kxo2a7SzzhhTKoC1jDQxnMKUgQixvy7e"}
#     result = get_data_from_api(request_url = Tumblr_search_url, identifier = "Tumblr", params_diction = Tumblr_search_params, expire_in_days = 7)
#     print(result) ## {'meta': {'status': 403, 'msg': 'Forbidden'}, 'response': 'Not authorized.'}

    
    # user1 = "thegoodvybe" # "mengyingzhangworld"
    # user1_search_url = get_posts_search_url(user1, "quote")
    # user1_search_params = {}
    # # Invoke functions
    # user1_result = get_data_from_api(request_url = user1_search_url, identifier = "Tumblr", params_diction = user1_search_params, expire_in_days = 7)
    #
    # user2 = "logicaldreamer" # "mengyingzhangworld" # "thegoodvybe"
    # user2_search_url = get_posts_search_url(user2, "quote")
    # user2_search_params = {}
    # # Invoke functions
    # user2_result = get_data_from_api(request_url = user2_search_url, identifier = "Tumblr", params_diction = user2_search_params, expire_in_days = 7)
    #
    # # See the result
    # print(type(user2_result))
    # print("=========================")
    # print(user2_result.get('response'))
    # print("=========================")
    # #print(result.get('response')['liked_posts'])
    #
    # user1_filename = "{}.csv".format(user1)
    # user2_filename = "{}.csv".format(user2)
    # write_files(user1_result.get('response')['posts'], user1_filename)
    # write_files(user2_result.get('response')['posts'], user2_filename)




