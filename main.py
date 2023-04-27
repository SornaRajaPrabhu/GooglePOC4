from flask import Flask
import requests
import json
import pandas as pd
from io import StringIO
import tensorflow as tf
import numpy as np

app = Flask(__name__)

@app.route('/')
def mainWork():
    username = "prabhu@relanto.ai"
    password = "Anaplan@April2023"
    
    auth_url = 'https://auth.anaplan.com/token/authenticate'
    auth_json = requests.post(
        url=auth_url,
        auth=(username, password)
    ).json()
    if auth_json['status'] == 'SUCCESS':
        authToken = 'AnaplanAuthToken ' + auth_json['tokenInfo']['tokenValue']
        print("19" + auth_json['status'])
        
        '''Token Validation'''
        auth_url = 'https://auth.anaplan.com/token/validate'
        auth_json2 = requests.get(
            url=auth_url,
            headers={
                'Authorization': authToken
            }
        ).json()
        print("29" + auth_json2['status'])
        if auth_json2['status'] == 'SUCCESS':
            expiresAt = auth_json2['tokenInfo']['expiresAt']
            print("32" + auth_json2['status'])
            
            ExportProcess = "Export_from_anaplan"
        
            '''Getting Process from Anaplan'''
            auth_url = 'https://api.anaplan.com/2/0/workspaces/8a868cdc7bd6c9ae017be5b938c83112/models/8B4052CB2DBE4E6AAEF8E96B968EFCCD/processes'
            auth_json3= requests.get(
                url=auth_url,
                headers={
                    'Authorization': authToken
                }
            ).json()
            print("44" + auth_json3['status']['message'])
            if auth_json3['status']['message'] == 'Success':
                for process in auth_json3['processes']:
                    if ExportProcess == process['name']:
                        processID = process['id']
                        print("49" + processID)
                        '''Starting the Process'''
                        auth_url = f"https://api.anaplan.com/2/0/workspaces/8a868cdc7bd6c9ae017be5b938c83112/models/8B4052CB2DBE4E6AAEF8E96B968EFCCD/processes/{processID}/tasks"
                        auth_json4 = requests.post(
                            url=auth_url,
                            headers={
                                'Authorization': authToken,
                                'Content-type': 'application/json'
                            },
                            data = json.dumps({'localeName': 'en_US'})
                        ).json()
                        print("60"+auth_json4['status']['message'])
                        if auth_json4['status']['message'] == 'Success':
                            taskID = auth_json4['task']['taskId']
                            print("63"+taskID)
                            '''Checking the Status of the Process'''
                            Flag = True
                            while Flag:
                                auth_url = f"https://api.anaplan.com/2/0/workspaces/8a868cdc7bd6c9ae017be5b938c83112/models/8B4052CB2DBE4E6AAEF8E96B968EFCCD/processes/{processID}/tasks/{taskID}"
                                auth_json5 = requests.get(
                                    url=auth_url,
                                    headers={
                                        'Authorization': authToken,
                                        'Content-type': 'application/json'
                                    }
                                ).json()
                                if auth_json5['task']['currentStep'] == "Failed.":
                                    print("Failed")
                                elif auth_json5['task']['currentStep'] != "Complete.":
                                    print(auth_json['task']['currentStep'])
                                elif auth_json5['task']['currentStep'] == "Complete.":
                                    print("Complete")
                                    Flag = False
                            
            '''Get files from anaplan'''
            url = f"https://api.anaplan.com/2/0/workspaces/8a868cdc7bd6c9ae017be5b938c83112/models/8B4052CB2DBE4E6AAEF8E96B968EFCCD/files/"
            getFileData = requests.get(
                url = url,
                headers = {
                    'Authorization': authToken
                }
            )
            getFileData_json = getFileData.json()
            print("92"+ getFileData_json['status']['message'])

            if getFileData_json['status']['message'] == 'Success':
                file_info = getFileData_json['files'];
                
                for file in file_info:
                    if file['name'] == "Google_Demo.csv":
                        fileID = file['id']
                        url = f"https://api.anaplan.com/2/0/workspaces/8a868cdc7bd6c9ae017be5b938c83112/models/8B4052CB2DBE4E6AAEF8E96B968EFCCD/files/{fileID}/chunks/"
                        getChunk = requests.get(
                            url,
                            headers = {
                                'Authorization': authToken,
                                "Content-Type": "application/json"
                            }
                        )
                        getChunk = getChunk.json()
                        if getChunk['status']['message'] == "Success":
                            print(f"Getting the chunk count of {file['id']} COMPLETED")
                            for chunk in getChunk['chunks']:
                                url = f"https://api.anaplan.com/2/0/workspaces/8a868cdc7bd6c9ae017be5b938c83112/models/8B4052CB2DBE4E6AAEF8E96B968EFCCD/files/{fileID}/chunks/{chunk['id']}"
                                getChunk = requests.get(
                                    url,
                                    headers = {
                                        'Authorization': authToken,
                                        "Content-Type": "application/json"
                                    }
                                )
                                data = pd.read_csv(StringIO(getChunk.text), sep=",")#, index_col=['Time'])
                                #print(data)
                                data=data[:52]

                                data['Time'] = pd.to_datetime(data['Time'], format='%b %y')
                                data['Time'] = data['Time'].apply(lambda x: x.timestamp())
                                train_data=data[:43]
                                test_data=data[43:52]
                                X_train = train_data['Time'].values.reshape(-1, 1)
                                y_train = train_data['Sales'].values.reshape(-1, 1)
                                X_test = test_data['Time'].values.reshape(-1, 1)
                                y_test = test_data['Sales'].values.reshape(-1, 1)
                                model = tf.keras.models.Sequential([
                                  tf.keras.layers.Dense(units=1, input_shape=[1])
                                ])

                                model.compile(optimizer=tf.keras.optimizers.Adam(1e-2), loss='mse')

                                history = model.fit(X_train, y_train, epochs=800)


                                last_date = pd.to_datetime(train_data['Time'].max(), unit='s')
                                next_dates = pd.date_range(start=last_date, periods=18, freq='MS')
                                next_dates_unix = next_dates.map(lambda x: x.timestamp())
                                y_new = model.predict(next_dates_unix.values.reshape(-1, 1))
                                test_data_upd=np.append(test_data['Sales'],([0]*9))
                                predictions = pd.DataFrame({'Time': next_dates,'Sales':test_data_upd ,'Predict': y_new.flatten()//1})

                                predictions.set_index('Time',inplace=True)
                                #predictions.to_csv('Google_Demo_import.csv')
                             
                                #df['Predict'] = 5
                csv = predictions.to_csv()
                print(csv)
                
                for file in file_info:
                    if file['name'] == "Google_Demo_import.csv":
                        fileID = file['id']
                        file['chunkCount'] = -1
                        fileData = file
                        url = f'https://api.anaplan.com/2/0/workspaces/8a868cdc7bd6c9ae017be5b938c83112/models/8B4052CB2DBE4E6AAEF8E96B968EFCCD/files/{fileID}'
                        getFileData1 = requests.post(
                            url = url,
                            headers = {
                                'Authorization': authToken,
                                'Content-Type': 'application/json'
                            },
                            json = fileData
                        )
                        getFileData1 = getFileData1.json()

                        if getFileData1['status']['message'] == 'Success':
                            print(f"Setting chunk count to -1 for {file['name']} COMPLETED")
                        
                        #csv = df.to_csv()
                        tempFileName = file['name']
                        fileID = file['id']

                        url = f'https://api.anaplan.com/2/0/workspaces/8a868cdc7bd6c9ae017be5b938c83112/models/8B4052CB2DBE4E6AAEF8E96B968EFCCD/files/{fileID}/chunks/0'
                        requests.put(
                            url,
                            headers = {
                                'Authorization': authToken,
                                'Content-Type': 'application/octet-stream'
                            },
                            data = csv
                        )
                        print(f"'{tempFileName}' Upload Completed")
                        
                        url = f'https://api.anaplan.com/2/0/workspaces/8a868cdc7bd6c9ae017be5b938c83112/models/8B4052CB2DBE4E6AAEF8E96B968EFCCD/files/{fileID}/complete'
                        fileCompleteResponse = requests.post(
                        url,
                        headers = {
                            'Authorization': authToken,
                            'Content-Type': 'application/json'
                        },
                        json = file
                        )
                        fileCompleteResponse = fileCompleteResponse.json()

                        if fileCompleteResponse['status']['message'] == "Success":
                            print(f"{tempFileName} started MARKED as complete")
            
            '''Getting Process from Anaplan'''
            auth_url = 'https://api.anaplan.com/2/0/workspaces/8a868cdc7bd6c9ae017be5b938c83112/models/8B4052CB2DBE4E6AAEF8E96B968EFCCD/processes'
            auth_json3= requests.get(
                url=auth_url,
                headers={
                    'Authorization': authToken
                }
            ).json()
            print("180" + auth_json3['status']['message'])
            if auth_json3['status']['message'] == 'Success':
                for process in auth_json3['processes']:
                    if "Import_to_anaplan" == process['name']:
                        processID = process['id']
                        print("185" + processID)
                        '''Starting the Process'''
                        auth_url = f"https://api.anaplan.com/2/0/workspaces/8a868cdc7bd6c9ae017be5b938c83112/models/8B4052CB2DBE4E6AAEF8E96B968EFCCD/processes/{processID}/tasks"
                        auth_json4 = requests.post(
                            url=auth_url,
                            headers={
                                'Authorization': authToken,
                                'Content-type': 'application/json'
                            },
                            data = json.dumps({'localeName': 'en_US'})
                        ).json()
                        print("196"+auth_json4['status']['message'])
                        if auth_json4['status']['message'] == 'Success':
                            taskID = auth_json4['task']['taskId']
                            print("199"+taskID)
                            '''Checking the Status of the Process'''
                            Flag = True
                            while Flag:
                                auth_url = f"https://api.anaplan.com/2/0/workspaces/8a868cdc7bd6c9ae017be5b938c83112/models/8B4052CB2DBE4E6AAEF8E96B968EFCCD/processes/{processID}/tasks/{taskID}"
                                auth_json5 = requests.get(
                                    url=auth_url,
                                    headers={
                                        'Authorization': authToken,
                                        'Content-type': 'application/json'
                                    }
                                ).json()
                                if auth_json5['task']['currentStep'] == "Failed.":
                                    print("Failed")
                                elif auth_json5['task']['currentStep'] != "Complete.":
                                    print(auth_json['task']['currentStep'])
                                elif auth_json5['task']['currentStep'] == "Complete.":
                                    print("Complete")
                                    Flag = False
    return "Integration Ran Successfull"
if __name__ == '__main__':
    app.run()