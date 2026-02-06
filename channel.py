# -*- encoding: utf-8 -*-

import scrapetube
from datetime import datetime
import dateutil.parser
import sys
import requests, json
from zoneinfo import ZoneInfo

class Program():
    def __init__(self, idchannel, urlchannel, youtubeKey, tz, dateFormats):
        self.idchannel = idchannel
        self.urlchannel = urlchannel
        self.youtubeKey = youtubeKey
        self.tzinfo = ZoneInfo(tz)
        self.dateFormats = dateFormats
        
        self.initLoggingFile()
        self.initResultFile()
            
    def initLoggingFile(self):
        loggingfilename = "channel_" + self.idchannel
        self.loggingfile = open(loggingfilename + ".log", "a", encoding="utf-8")
    
    def initResultFile(self):
        dateNow = self.getDateNow()
        resultfilename = "channel_" + self.idchannel + "_" + dateNow['dateFileString'] + ".txt"
        self.resultfile = open(resultfilename, "w", encoding="utf-8")
    
    def getDateNow(self):
        timestamp_now = datetime.now().timestamp()
        date = datetime.fromtimestamp(timestamp_now, self.tzinfo)
        dateString = date.strftime(self.dateFormats['dateString'])
        dateDBString = date.strftime(self.dateFormats['dateDBString'])
        dateFileString = date.strftime(self.dateFormats['dateFileString'])
        
        dateNow = {"dateString": dateString, "dateDBString": dateDBString, "dateFileString": dateFileString}
        
        return dateNow

    def writelog(self, message):
        dateNow = self.getDateNow()
        self.loggingfile.write(dateNow["dateString"] + " : " + message + "\n")
        # Write in real time
        self.loggingfile.flush()
            
    def writeresult(self, message):
        self.resultfile.write(message)
        # Write in real time
        #self.resultfile.flush()

    # Used when errors/exceptions occured and when we want to exit right now
    def exitProgram(self):
        self.writelog("Execution had errors")
        self.writelog("Ending program")
        self.clean()
        sys.exit(1)
    
    # Used at the end of program without errors/exceptions and when errors/exception occured
    def clean(self):
        try:
            # Close Files
            self.loggingfile.close()
            self.resultfile.close()
        except Exception as e:
            print("Error cleaning up : " + str(e))
    
    def main(self):
        print("Starting program")
        self.writelog("Starting program")

        # Get infos of channel
        channelInfosURL = "https://www.googleapis.com/youtube/v3/channels?key=" + self.youtubeKey + "&id=" + self.idchannel + "&part=brandingSettings,contentDetails,contentOwnerDetails,id,localizations,snippet,statistics,status,topicDetails"
        print(channelInfosURL)
        try:
            response = requests.get(channelInfosURL)
            if response.status_code == 200:
                channelInfosResponse = response.text
                channel_json = json.loads(channelInfosResponse)
            else:
                print(f"[×] channel={self.idchannel} Response of channelInfosURL {channelInfosURL} isn't OK : {response.status_code} {response.text}")
                self.writelog(f"[×] channel={self.idchannel} Response of channelInfosURL {channelInfosURL} isn't OK : {response.status_code} {response.text}")
                self.exitProgram()
        except Exception as e:
            print(f"[×] channel={self.idchannel} Error channelInfosURL {channelInfosURL} : {e}")
            self.writelog(f"[×] channel={self.idchannel} Error channelInfosURL {channelInfosURL} : {e}")
            self.exitProgram()
                
        item = channel_json.get('items')[0]
        snippet = item.get('snippet')
        handle = snippet.get('customUrl')[1:len(snippet.get('customUrl'))]
        self.urlchannel = "https://www.youtube.com/@"  + handle

        dateChannel = snippet.get('publishedAt')
        dateChannel_object = dateutil.parser.isoparse(dateChannel)
        dateChannel_text = dateChannel_object.astimezone(self.tzinfo).strftime(self.dateFormats['dateString'])

        dateNow = self.getDateNow()        
        # Get thumbnail image
        thumbnails = snippet.get('thumbnails')
        thumbnail_item = thumbnails.get('high')
        thumbnail_url = thumbnail_item.get('url')
        try:
            response = requests.get(thumbnail_url, stream = True)
            if response.status_code == 200:
                thumbnailInfosResponse = response.content
                filethumbnail = "channel_" + self.idchannel + "_" + dateNow['dateFileString'] + "_thumbnail.jpeg"
                fthumbnail = open(filethumbnail, "wb")
                fthumbnail.write(thumbnailInfosResponse)
                fthumbnail.close()
            else:
                print(f"[×] idchannel={self.idchannel} Response of thumbnail_url {thumbnail_url} isn't OK : {response.status_code} {response.text}")
                self.writelog(f"[×] idchannel={self.idchannel} Response of thumbnail_url {thumbnail_url} isn't OK : {response.status_code} {response.text}")
                self.exitProgram()
        except Exception as e:
            print(f"[×] idchannel={self.idchannel} Error thumbnail_url {thumbnail_url} : {e}")
            self.writelog(f"[×] idchannel={self.idchannel} Error thumbnail_url {thumbnail_url} : {e}")
            self.exitProgram()
            
        # Get banner image
        if "image" in item.get('brandingSettings'):
            bannerExternalUrl = item.get('brandingSettings').get('image').get('bannerExternalUrl')
            try:
                response = requests.get(bannerExternalUrl, stream = True)
                if response.status_code == 200:
                    bannerInfosResponse = response.content
                    filebanner = "channel_" + self.idchannel + "_" + dateNow['dateFileString'] + "_banner.jpeg"
                    fbanner = open(filebanner, "wb")
                    fbanner.write(bannerInfosResponse)
                    fbanner.close()
                else:
                    print(f"[×] idchannel={self.idchannel} Response of bannerExternalUrl {bannerExternalUrl} isn't OK : {response.status_code} {response.text}")
                    self.writelog(f"[×] idchannel={self.idchannel} Response of bannerExternalUrl {bannerExternalUrl} isn't OK : {response.status_code} {response.text}")
                    self.exitProgram()
            except Exception as e:
                print(f"[×] idchannel={self.idchannel} Error bannerExternalUrl {bannerExternalUrl} : {e}")
                self.writelog(f"[×] idchannel={self.idchannel} Error bannerExternalUrl {bannerExternalUrl} : {e}")
                self.exitProgram()
        
        title = snippet.get('title')
        description = snippet.get('description')

        stats = item.get('statistics')
        viewCount = stats.get('viewCount')
        subscriberCount = stats.get('subscriberCount')
        videoCount = stats.get('videoCount')

        self.writeresult("Channel " + self.urlchannel + " id : " + self.idchannel)
        self.writeresult("\n\n")

        print("Title : " + title)
        self.writeresult("Title : " + title)
        self.writeresult("\n")
        print("Description : " + description)
        self.writeresult("Description : " + description)
        self.writeresult("\n")
        print("Date : " + dateChannel_text)
        self.writeresult("Date : " + dateChannel_text)
        self.writeresult("\n")
        print("viewCount : " + viewCount)
        self.writeresult("viewCount : " + viewCount)
        self.writeresult("\n")
        print("subscriberCount : " + subscriberCount)
        self.writeresult("subscriberCount : " + subscriberCount)
        self.writeresult("\n")
        print("videoCount : " + videoCount)
        self.writeresult("videoCount : " + videoCount)
        self.writeresult("\n\n")

        print("Execution was OK")
        self.writelog("Execution was OK")
        print("Ending program")
        self.writelog("Ending program")
        self.clean()

if __name__ == "__main__":
    # Youtube
    urlchannel = "https://www.youtube.com/@your_channel"
    idchannel = '' # Found channel id on Youtube by clicking "Share channel" then "Copy channel ID"
    youtubeKey = '' # YouTube API Key from Google Cloud, see https://helano.github.io/help.html
    # Format
    tz = "Europe/Paris"
    dateFormats = {"dateString": "%d/%m/%Y %H:%M:%S", "dateDBString": "%Y-%m-%d %H:%M:%S", "dateFileString": "%d%m%Y%H%M%S"}

    # Launch
    program = Program(idchannel, urlchannel, youtubeKey, tz, dateFormats)
    program.main()
    

