import os
import datetime
import json


OFFLINE_DATA_PATH = os.getenv('OFFLINE_DATA_PATH', '/home/pi/Documents/IotAdapter/offlinedata')

class OfflineData(object):
    def __init__(self):

        # check if offline data folder exists
        # if not create one
        if not os.path.isdir(OFFLINE_DATA_PATH):
            os.makedirs(OFFLINE_DATA_PATH)

        
    def save_message(self, message):
        try:
            f = open(OFFLINE_DATA_PATH + '/' + datetime.today().strftime('%Y-%m-%d').replace('-', '_') + '.json', 'a')
            for row in message:
                f.write(json.dumps(row) + '\n')
            f.close()
        except Exception as e:
            print('[OfflineData] Offline Data is not writeable')
            print(e)

    def _interprete_messages_complete(self, f):
        # read file
        file_data_lines = f.readlines()
        try:
            # need to convert json

            # add , at the end of each line
            # and bracket around the whole file
            readable_json_string = f"{{ {file_data_lines.join(',\n')} }}"

            # convert all messages of this day to json
            messages_in_file = json.loads(readable_json_string)


            return messages_in_file
        except:
            # in failure return empty object
            return []

    def interprete_offline_data(self):
        # check if i can open folder
        if not os.path.isdir(OFFLINE_DATA_PATH):
            return 0
        
        for file in os.listdir(OFFLINE_DATA_PATH):
            file_path = os.path.join(OFFLINE_DATA_PATH, file)


            messages_in_file = []
            try:
                # read file
                f = open(file_path, 'r')

                # try to read file in complete                
                messages_in_file = self._interprete_messages_complete(f)

                # read every message
                # if message in file has one error                
                if not len(messages_in_file):
                    pass

                f.close()

                # convert all messages of this day to json
               # messages_in_file = json.loads(file_data)
                

            except:
                pass


            

        pass
    
    

    def _build_offline_message_block(file):

        messages = []
        message = []

        f = open(OFFLINE_DATA_PATH + '/' + file, 'r')
        
        error_in_message_block = False
        
        # go throung all lines in one file
        for line in f.readlines():
            
            # check if line starts like a json would start
            if not line.startswith('{'):
                continue
            
            try:
                conv_line = json.loads(line)

                # if new line is mad start new message block
                if (conv_line['name'] == 'mad' or conv_line['name'] == 'MAD'):
                # only add if message block has entrys
                if len(message):
                    messages.append(message)
                    
                # then clear message block
                message = []
                
                # also there can be no errors in the message block 
                error_in_message_block = False
                
                
                if not error_in_message_block:
                message.append(conv_line)
                
            except Exception as e:
                print(e)
                # this means one line in the message block is not a vaild JSON
                error_in_message_block = True
                
                # prevent deleting this file
                success_sending_data = False

        # end of loop
        
        # close file to prevent crossing
        f.close()
        
        # append last message block to the whole message
        messages.append(message)
        
        return messages
    
    def delete_offline_data():

      
        
        pass