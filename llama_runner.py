import os
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2

PAT = os.getenv("CLARIFAI_TOKEN")
USER_ID = 'meta'
APP_ID = 'Llama-2'
MODEL_ID = 'llama2-70b-chat'
MODEL_VERSION_ID = '6c27e86364ba461d98de95cddc559cb3'

channel = ClarifaiChannel.get_grpc_channel()
stub = service_pb2_grpc.V2Stub(channel)
metadata = (('authorization', 'Key ' + PAT),)
userDataObject = resources_pb2.UserAppIDSet(user_id=USER_ID, app_id=APP_ID)

def pretendToSanitize(text):
    return text.replace("[INST]", "").replace("[/INST]", "").replace("<<SYS>>", "").replace("<</SYS>>", "").replace("<s>", "")

def runPrompt(sys, prompt):
    post_model_outputs_response = stub.PostModelOutputs(
        service_pb2.PostModelOutputsRequest(
            user_app_id=userDataObject,
            model_id=MODEL_ID,
            version_id=MODEL_VERSION_ID,
            inputs=[
                resources_pb2.Input(
                    data=resources_pb2.Data(
                        text=resources_pb2.Text(
                            raw=f"<s>[INST]<<SYS>>{sys}<</SYS>>{prompt}[/INST]"
                        )
                    )
                )
            ]
        ),
        metadata=metadata
    )
    if post_model_outputs_response.status.code != status_code_pb2.SUCCESS:
        print(post_model_outputs_response.status)
        raise Exception(f"Post model outputs failed, status: {post_model_outputs_response.status.description}")

    # Since we have one input, one output will exist here
    output = post_model_outputs_response.outputs[0]

    return output.data.text.raw

# Returns a (sys, prompt) tuple with details from the given input
# Meant to be used with runPrompt
def createPrompt(colors, concepts, brands):
    sys = """You are an AI engine that takes the detected features of an article of clothing and generates a description of it in natural language.
Your message should consist of two paragraphs: one with the description, and one with a chromatically paired "this would go well with" recommendation.
Begin the description with the character ^ and begin the recommendation with the character ~"""
    prompt = """"""

    colors_str = "No specific colors were detected"
    if len(colors) > 0:
        colors_str = "Colors: " + ", ".join([color.name for color in colors])
    concepts_str = "Unknown article of clothing"
    if len(concepts) > 0:
        concepts_str = "Concepts: " + ", ".join([concept.name for concept in concepts])
    brands_str = "No brands were detected"
    if len(brands) > 0:
        brands_str = "Brand markings: " + ", ".join([brand.name for brand in brands])

    prompt += "\n".join([colors_str, concepts_str, brands_str])
    
    # 200iq sanitization
    sys = pretendToSanitize(sys)
    prompt = pretendToSanitize(prompt)

    return (sys, prompt)