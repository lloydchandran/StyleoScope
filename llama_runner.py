import os
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2

# Your PAT (Personal Access Token) can be found in the portal under Authentification
PAT = os.getenv("CLARIFAI_TOKEN")
# Specify the correct user_id/app_id pairings
# Since you're making inferences outside your app's scope
USER_ID = 'openai'
APP_ID = 'chat-completion'
# Change these to whatever model and text URL you want to use
MODEL_ID = 'GPT-4'
MODEL_VERSION_ID = 'ad16eda6ac054796bf9f348ab6733c72'

channel = ClarifaiChannel.get_grpc_channel()
stub = service_pb2_grpc.V2Stub(channel)
metadata = (('authorization', 'Key ' + PAT),)
userDataObject = resources_pb2.UserAppIDSet(user_id=USER_ID, app_id=APP_ID)

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
                            raw=f"[INST]<<SYS>>{sys}<</SYS>>{prompt}[/INST]"
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
    sys = """You are given the details of an article of clothing, which were detected automatically.
You should come up with a short description of the item, oriented towards potential buyers.
Make sure to use the natural language names of the detected colors, concepts, and brands, not the actual detected names.
Provide a "This goes well with" section at the end, with some chromatically paired suggestions.
"""
    prompt = """"""

    colors_str = "No specific colors were detected"
    if len(colors) > 0:
        colors_str = "Colors: " + ", ".join([color.hex for color in colors])
    concepts_str = "Unknown article of clothing"
    if len(concepts) > 0:
        concepts_str = "Concepts: " + ", ".join([concept.name for concept in concepts])
    brands_str = "No brands were detected"
    if len(brands) > 0:
        brands_str = "Brand markings: " + ", ".join([brand.name for brand in brands])

    prompt += "\n".join([colors_str, concepts_str, brands_str])
    
    # 200iq sanitization
    sys = sys.replace("[INST]", "").replace("[/INST]", "").replace("<<SYS>>", "").replace("<</SYS>>", "")
    prompt = prompt.replace("[INST]", "").replace("[/INST]", "").replace("<<SYS>>", "").replace("<</SYS>>", "")

    return (sys, prompt)