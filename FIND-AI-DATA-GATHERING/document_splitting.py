import re
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient
import os

AZURE_STORAGE_CONNECTION_STRING = 'DefaultEndpointsProtocol=https;AccountName=adpaipocukssa;AccountKey=5kHH8xHh7KzuUBPR2St2FYFpGZLRYP8+g1EftM857UnpQk9cDswC1cj5Mton+ifVqdi9bVC2aPOq+AStRQC80g==;EndpointSuffix=core.windows.net'
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
input_container_name = 'find-ai-poc-scraped-webpages'
output_container_name = 'find-ai-indexed-webpages'
local_path = "./blob_download_data"

if os.path.isdir(local_path) == False:
  os.mkdir(local_path)


def download_blobs_to_string(blob_service_client: BlobServiceClient, container_name: str) -> (list):
    container_client = blob_service_client.get_container_client(container=input_container_name)
    blob_docs = container_client.list_blob_names()
    
    downloaded_texts = []
    
    for blob_name in blob_docs:
        blob_client = blob_service_client.get_blob_client(container=input_container_name, blob=blob_name)
        downloader = blob_client.download_blob(max_concurrency=1, encoding='utf-8')
        blob_text = downloader.readall()
        downloaded_texts.append((blob_name, blob_text))
        #split_markdown_by_headings(blob_text, blob_name)
    return downloaded_texts


def split_markdown_by_headings(doc_title, markdown_content):
  # Define the regular expression pattern to match H1 and H2 headings
  pattern = r'((?<!#)#{1,2}(?!#).*)'

  # Split the Markdown text based on the headings
  sections = re.split(pattern, markdown_content)
  
  
  url = sections[0]
  sections = sections[1:]
  # Combine each heading with its corresponding text
  combined_sections = []
  for i in range(0, len(sections), 2):
    heading = sections[i].strip()  # Get the heading from sections[i]
    heading = heading.replace("#", "")
    text = sections[i + 1].strip() if i + 1 < len(
        sections) else ''  # Get the text from sections[i + 1] if it exists, otherwise use an empty string
    
    output_content_chunk = str(url) + "\n" + str(text)
    
    chunk_title = doc_title.replace(".txt", (" --" + str(heading) + ".txt"))
    doc_chunk_tup = (chunk_title, output_content_chunk)
    combined_sections.append(doc_chunk_tup)  # Add the combined section to the list

  return combined_sections

def write_chunk_blobs():
    blob_plaintext_list = download_blobs_to_string(blob_service_client, input_container_name)
    
    for blob in blob_plaintext_list:
        blob_chunked_tups = split_markdown_by_headings(blob[0], blob[1])
        for chunk in blob_chunked_tups:
            upload_file_path = os.path.join(local_path, chunk[0])
      
            file = open(
                file = upload_file_path,
                mode = 'w'
            )
            
            file.write(chunk[1])
            file.close()
            
            blob_client = blob_service_client.get_blob_client(container = output_container_name,
                                                                blob = chunk[0])
            
            print("\nUploading Chunk to Azure Storage as blob:\n\t" + chunk[0])
            
            with open(file = upload_file_path, mode = 'rb') as data:
                blob_client.upload_blob(data, overwrite = True)


write_chunk_blobs()


test_str = """https://www.gov.uk/countryside-stewardship-grants/nectar-flower-mix-ab1
## How much will be paid
 
�739 per hectare (ha)
 
## Where to use this option
 
Available for Countryside Stewardship Mid Tier and Higher Tier
 
  * Whole or part parcel
  * Rotational
 
 
Only on:
 
  * arable land
 
  * temporary grass
 
  * bush orchards
 
 
 
## Where this option cannot be used
 
  * On organic land or on land in conversion to organic status
 
 
## How this option will benefit the environment
 
It provides areas of flowering plants to boost essential food sources for beneficial pollinators such as bumble bees, solitary bees, butterflies and hoverflies.
 
## Aims
 
If you�re selected for a site visit, we will check that delivery of the aims is being met and the prohibited activities have not been carried out. This will ensure the environmental benefits are being delivered.
 
Establish in blocks or strips between 1 March and 15 September by sowing a grass-free seed mix which contains a minimum of 6 flower species. At least 2 of these must be from the following list.
 
  * Common knapweed
  * Musk mallow
  * Oxeye daisy
  * Wild carrot
  * Yarrow
 
 
Once established in the first year, the seed mix, will provide a supply of pollen and nectar rich flowers.
 
Management will ensure there is sustained flowering throughout the spring and summer.
 
In the winter the whole plot of flowering plants will be cut or grazed, and the dead material removed, in preparation for regrowth during the spring.
 
## Prohibited activities
 
To achieve the aims and deliver the environmental benefits, **do not** carry out any of the following activities:
 
  * graze between 15 March and 31 August
 
  * allow a single species to exceed 50% of the total seed mix by weight.
 
 
 
On your annual claim you will be asked to declare that you **have not** carried out any prohibited activities.
 
## Recommended management
 
To assist you in achieving the aims and deliver the environmental benefits for this option, we recommend that you use best practice.
 
In the first 12 months after sowing you can regularly cut, to help the sown species to establish.
 
You then manage established nectar flower mix plots as follows.
 
  * Rotationally cut half (50%) of the plot area each year between 15 May and 15 June � do not cut the same area in successive years
 
  * Cut the whole plot (100%) each year between 15 September and 30 March
 
 
 
Remove or shred cuttings to prevent weed ingress and patches of dead material developing.
 
## Keeping records
 
Where there�s uncertainty about whether or not the aims of the options have been delivered, we will take into account any records or evidence you may have kept to demonstrate delivery of the aims of the option. This will include any steps you�ve taken to follow the recommended management set out above. It�s your responsibility to keep such records if you want to rely on these to support your claim.
 
  * Seed invoices
  * Field operations at the parcel level, including associated invoices
  * Stock records to show grazing activity on parcels in particular to cover the period where grazing is prohibited.
  * Photographs of the established mixture
 
 
## Additional guidance and advice
 
The following advice is helpful, but they are not requirements for this item.
 
### Pick the right location
 
Use lower-yielding areas with a sunny aspect, facing south or south-southwest.
 
Avoid planting under overhanging trees, next to tall hedges or on land facing north or east. Leave access to surrounding crops to allow for management.
 
### Block and plot sizes
 
Use wide margins and big blocks between 0.25ha and 0.5ha. This lets insects move to safety when fields are being sprayed.
 
Spacing five 0.5ha patches evenly within 100ha meets the food needs of many pollinators.
 
### What to sow
 
A seed mix which contains both shorter-lived legumes and longer-lived wild flower species delivers an extended supply of pollen and nectar from late spring through to the autumn for beneficial insects such as bees, butterflies, hoverflies and moths.
 
You can sow the following example mix on a range of soil types.
 
Flower species | % inclusion rate  
---|---  
Alsike clover | 10  
Bird�s-foot trefoil | 10  
Black medick | 5  
Common vetch | 40  
Early flowering red clover | 10  
Late flowering red clover | 10  
Lucerne | 5  
Sweet clover | 5  
Common knapweed | 1.5  
Musk mallow | 1  
Oxeye daisy | 1  
Wild carrot | 1  
Yarrow | 0.5  
Total | 100  
Sow the seed mix at 15 kg/ha.
 
On light free draining soils you can replace common vetch with sainfoin.
 
Avoid short-term mixes that do not include knapweed or mallow as they will not supply pollinators with long-term food sources for years 4 and 5 of the agreement.
 
### How to sow
 
Sow by broadcasting seeds rather than drilling, when the soil is warm and moist. Use a ring roll before and after sowing. Check regularly for slug damage.
 
### Management
 
Cut emerging flowers and weeds at least twice in year 1, and up to 4 times if necessary where the soil is particularly fertile. Regular cutting prevents weeds smothering the slow-growing flowers so all sown species can establish successfully.
 
Plots may be grazed between 1 September and 14 March, but make sure that no poaching or soil compaction by livestock takes place. Supplementary feeding could result in poaching and soil compaction, so should be avoided.
 
Remember you must keep nectar plots until at least 31 December in year 5 of the agreement.
 
### Integrated Pest Management (IPM)
 
This option can form part of an IPM approach to prevent the establishment of pests, weeds and diseases. If successful, appropriate and within proximity of cropped areas, these may limit the need for the use of Plant Protection Products and enhance wildlife and biodiversity on your holding. Read information on IPM at AHDB (Agriculture and Horticulture Development Board) Integrated Pest Management and LEAF (Linking Environment and Farming).
 
### Biodiversity
 
This option has been identified as being beneficial for biodiversity. All Countryside Stewardship habitat creation, restoration and management options are of great significance for biodiversity recovery, as are the wide range of arable options in the scheme. Capital items and supplements can support this habitat work depending on the holding�s situation and potential.
 
The connectivity of habitats is also very important and habitat options should be linked wherever possible. Better connectivity will allow wildlife to move/colonise freely to access water, food, shelter and breeding habitat, and will allow natural communities of both animals and plants to adapt in response to environmental and climate change.
 
## Further information
 
Order the �Growing farm wildlife� DVD from Natural England which gives a step-by-step approach to sowing nectar flower mixtures.
 
Read Countryside Stewardship: get funding to protect and improve the land you manage to find out more information about Mid Tier and Higher Tier including how to apply.
 
Published 2 April 2015   
Last updated 4 January 2024"""

#encoded_test = test_str.encode('utf-8')


#print(encoded_test)