import os
import re
import streamlit as st
import pandas as pd
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

from custom_types import ColorResult, Concept, RegionResult
from llama_runner import createPrompt, runPrompt
from stable_diffusion import createImage

USER_ID = 'pizzahunter2000'
PAT = os.getenv("CLARIFAI_TOKEN")
APP_ID = 'StyloScope'
WORKFLOW_ID = 'workflow-c4a9f1'
channel = ClarifaiChannel.get_grpc_channel()
stub = service_pb2_grpc.V2Stub(channel)
metadata = (('authorization', 'Key ' + PAT),)
userDataObject = resources_pb2.UserAppIDSet(user_id=USER_ID, app_id=APP_ID)

def runWorkflow(file):
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

    results = post_workflow_results_response.results[0]
    return results

def getColors(results):
    colorResults = []
    for output in results.outputs:
        if output.model.id == "color-recognition":
            for color in output.data.colors:
                colorResults.append(ColorResult(color.raw_hex, color.w3c, color.value))
    return colorResults

def getRegionsWithConceptsLogo(results):
    regionResults = []
    for output in results.outputs:
        if output.model.id == "logos-yolov5":
            for regions in output.data.regions:
                regionResult = RegionResult(regions.id, regions.region_info.bounding_box)
                for concept in regions.data.concepts:
                    regionResult.addConcept(Concept(concept.id, concept.name, concept.value))
                regionResults.append(regionResult)
    return regionResults

def getRegionsWithConcepts(results):
    regionResults = []
    for output in results.outputs:
        if output.model.id == "apparel-classification-v2":
            for regions in output.data.regions:
                regionResult = RegionResult(regions.id, regions.region_info.bounding_box)
                for concept in regions.data.concepts:
                    regionResult.addConcept(Concept(concept.id, concept.name, concept.value))
                regionResults.append(regionResult)
    return regionResults

if __name__ == "__main__":
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        results = runWorkflow(uploaded_file.read())
        colors = getColors(results)

        # Create a table of name and hex values
        st.write("## Colors")
        col1, col2 = st.columns([5, 7])
        with col1:
            st.image(Image.open(uploaded_file), use_column_width=True)
        with col2:
            st.data_editor(
                pd.DataFrame.from_records([{
                    'color': color.svg,
                    'name': color.name,
                    'hex': color.hex,
                    'prevalence': color.prevalence
                } for color in colors]),
                column_config={
                    "color": st.column_config.ImageColumn(),
                    "prevalence": st.column_config.ProgressColumn(
                        format="%.2f%%",
                        min_value=0,
                        max_value=1,
                    ),
                },
                hide_index=True,
            )

        st.write("## All Concepts")
        regions = getRegionsWithConcepts(results)
        with st.expander("Concept detection details"):
            st.write("## Regions")
            for region in regions:
                st.write(f"### {region.id}")
                st.image(region.drawBoundingBox(Image.open(uploaded_file)), use_column_width=True)
                st.table(pd.DataFrame.from_records([{
                    'name': concept.name,
                    'id': concept.id,
                    'confidence': f'{concept.confidence * 100:.2f}%'
                } for concept in region.concepts]))
        
        # Aggregate concepts
        allConcepts = {}
        for region in regions:
            for concept in region.concepts:
                if concept.id in allConcepts:
                    allConcepts[concept.id].confidence += concept.confidence
                else:
                    allConcepts[concept.id] = concept
        for concept in allConcepts.values():
            concept.confidence /= len(regions)
        
        # Remove concepts below 50% confidence
        allConcepts = {k: v for k, v in allConcepts.items() if v.confidence > 0.5}

        st.table(pd.DataFrame.from_records([{
            'name': concept.name,
            'id': concept.id,
            'confidence': f'{concept.confidence * 100:.2f}%'
        } for concept in allConcepts.values()]))

        # TODO: Display concepts as hashtags

        st.write("## All Brands")
        brands = getRegionsWithConceptsLogo(results)
        with st.expander("Brand detection details"):
            st.write("## Brands")
            for region in brands:
                st.write(f"### {region.id}")
                st.image(region.drawBoundingBox(Image.open(uploaded_file)), use_column_width=True)
                st.table(pd.DataFrame.from_records([{
                    'name': concept.name,
                    'id': concept.id,
                    'confidence': f'{concept.confidence * 100:.2f}%'
                } for concept in region.concepts]))
        
        # Aggregate brands
        allBrands = {}
        for region in brands:
            for concept in region.concepts:
                if concept.id in allBrands:
                    allBrands[concept.id].confidence += concept.confidence
                else:
                    allBrands[concept.id] = concept
        
        # TODO: Secondary filtering

        st.table(pd.DataFrame.from_records([{
            'name': concept.name,
            'id': concept.id,
            'confidence': concept.confidence
        } for concept in allBrands.values()]))

        st.write("## Synthesis")

        # Create and run prompt
        sys, prompt = createPrompt(colors, allConcepts.values(), allBrands.values())
        with st.expander("Prompt"):
            st.write("### System")
            st.write(sys)
            st.write("### Input Data")
            st.write(prompt)

        # Run prompt
        img_prompt = ''
        with st.spinner("Generating..."):
            response = runPrompt(sys, prompt)
            with st.expander("Raw response"):
                st.write(response)
            
            # Use a regex to extract the first paragraph starting with ^
            response += "\n\n"
            desc_pattern = r'\^\s?(.*?)(?=\n\n)'
            match = re.search(desc_pattern, response, re.DOTALL | re.MULTILINE)
            st.write("### Product Description")
            if match:
                st.write(match.group(1))
            else:
                st.error("No description found")
            
            rec_pattern = r'~\s?(.*?)(?=\n\n)'
            match = re.search(rec_pattern, response, re.DOTALL | re.MULTILINE)
            st.write("### Product Recommendation")
            if match:
                img_prompt = match.group(1)
                st.write(img_prompt)
            else:
                st.error("No recommendation found")

        # Use stable-diffusion to pair chromatically
        # with st.spinner("Visualizing..."):
        #     img = createImage(match.group(1))
        #     st.write(img)