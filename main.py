import json
import streamlit as st
import pandas as pd
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2

USER_ID = 'pizzahunter2000'
# Your PAT (Personal Access Token) can be found in the portal under Authentification
PAT = '18b597103b19450587f621929c41a137'
APP_ID = 'ReFashion001'
# Change these to make your own predictions
WORKFLOW_ID = 'workflow-c4a9f1'
IMAGE_URL = 'https://samples.clarifai.com/metro-north.jpg'

channel = ClarifaiChannel.get_grpc_channel()
stub = service_pb2_grpc.V2Stub(channel)
metadata = (('authorization', 'Key ' + PAT),)
userDataObject = resources_pb2.UserAppIDSet(user_id=USER_ID, app_id=APP_ID)

def doTheThing(file):
    post_workflow_results_response = stub.PostWorkflowResults(
        service_pb2.PostWorkflowResultsRequest(
            user_app_id=userDataObject,  
            workflow_id=WORKFLOW_ID,
            inputs=[
                resources_pb2.Input(
                    data=resources_pb2.Data(
                        image=resources_pb2.Image(
                            base64=file
                        )
                    )
                )
            ]
        ),
        metadata=metadata
    )
    if post_workflow_results_response.status.code != status_code_pb2.SUCCESS:
        print(post_workflow_results_response.status)
        raise Exception("Post workflow results failed, status: " + post_workflow_results_response.status.description)

    # We'll get one WorkflowResult for each input we used above. Because of one input, we have here one WorkflowResult
    results = post_workflow_results_response.results[0]
    return results


uploaded_file = st.file_uploader("Choose a file")
if uploaded_file is not None:
    results = doTheThing(uploaded_file.read())
    for output in results.outputs:
        if output.model.id == "color-recognition":
            for color in output.data.colors:
                st.write(color)
