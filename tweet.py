import getopt
import os
import sys
import configparser

import twitter

TWITTER_DM_LIMIT = 10000

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

class TweetRc(object):
    def __init__(self, config_path):
        self._config = None
        self.config_path = config_path

    def GetConsumerKey(self):
        return self._GetOption('consumer_key')

    def GetConsumerSecret(self):
        return self._GetOption('consumer_secret')

    def GetAccessKey(self):
        return self._GetOption('access_key')

    def GetAccessSecret(self):
        return self._GetOption('access_secret')
    
    def GetErrorNotifyUser(self):
        return self._GetOption('error_notify_user')

    def _GetOption(self, option):
        try:
            return self._GetConfig().get('Tweet', option)
        except:
            return None

    def _GetConfig(self):
        if not self._config:
            self._config = configparser.ConfigParser()
            self._config.read(os.path.expanduser(self.config_path))
        return self._config


class TwitterHandler():
    def __init__(self, config_path=f'{os.path.dirname(os.path.realpath(__file__))}/.tweetrc'):
        self.twitter_config = TweetRc(config_path)

        consumer_key =  self.twitter_config.GetConsumerKey()
        consumer_secret = self.twitter_config.GetConsumerSecret()
        access_key = self.twitter_config.GetAccessKey()
        access_secret = self.twitter_config.GetAccessSecret()

        if not consumer_key or not consumer_secret or not access_key or not access_secret:
            raise ValueError('Missing required twitter credentials')

        self._api = twitter.Api(consumer_key=consumer_key, consumer_secret=consumer_secret,
                          access_token_key=access_key, access_token_secret=access_secret)

    def tweet(self, message):
        return self._api.PostUpdate(message)

    def dm(self, message, to=None):
        if not to:
            to = self.twitter_config.GetErrorNotifyUser()

        recipient = self._api.GetUser(screen_name=to, return_json=True)

        responses = []
        for chunk in chunks(message, TWITTER_DM_LIMIT):
             responses.append(self._api.PostDirectMessage(chunk, user_id=recipient['id'], return_json=True) )

        return responses
