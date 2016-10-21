import lxml.etree as ET
import lxml.builder as builder
import uuid
import time
import sys
import subprocess
import os
from glob import glob
import pg
import hashlib 
from collections import OrderedDict
import csv

'''
Presumptions:
1. rawaudio.py is run first and a premis xml does not already exist or you get a uuid error
2. makedpx.py runs second
3. parent folder path is used for getting info on OE/filmographic number/source accession number
4. for now, makedpx.py requires a silly config file
5. lxml/ffmpeg/hashlib/md5deep/ififuncs/pyqt4 must all be installed
'''
def hashlib_md5(source_file,filename, manifest):   
   m = hashlib.md5()
   with open(str(filename), 'rb') as f:
       while True:
           buf = f.read(2**20)
           if not buf:
               break
           m.update(buf)
   md5_output = m.hexdigest()
   '''''
   commenting out as most other microservies will be making their own manifests anyhow. Still, two checksums are made per file right now which is terrible
   with open(manifest, "ab") as fo:
       fo.write(md5_output + '  ' + source_file.split(os.sep)[-1] + '/' + filename +  '\n')
   '''
   return md5_output

    
def add_value(value, element):
    element.text = value

    
def write_premis(doc, premisxml):
    with open(premisxml,'w') as outFile:
        doc.write(outFile,pretty_print=True)


def create_unit(index,parent, unitname):
    premis_namespace = "http://www.loc.gov/premis/v3"
    unitname = ET.Element("{%s}%s" % (premis_namespace, unitname))
    parent.insert(index,unitname)
    return unitname
    
    
def create_hash(filename):
    md5 = subprocess.check_output(['md5deep', filename])[:32]
    messageDigestAlgorithm.text = 'md5'
    messageDigest.text = md5
    return md5    


def get_input(filename):
    # Input, either file or firectory, that we want to process.
    input = filename
    # Store the directory containing the input file/directory.
    wd = os.path.dirname(os.path.abspath(input))
    # Change current working directory to the value stored as "wd"
    os.chdir(wd)
    # Store the actual file/directory name without the full path.
    file_without_path = os.path.basename(input)
    # Check if input is a file.
    # AFAIK, os.path.isfile only works if full path isn't present.
    if os.path.isfile(input):      
        video_files = []                       # Create empty list 
        video_files.append(file_without_path)  # Add filename to list
    # Check if input is a directory. 
    elif os.path.isdir(file_without_path):  
        os.chdir(file_without_path)
        video_files = (
            glob('*.tif') +
            glob('*.tiff') +
            glob('*.dpx') + 
            glob('*.wav')
            
        )
    # Prints some stuff if input isn't a file or directory.
    else: 
        print "Your input isn't a file or a directory."   
    return video_files


def make_premis(source_file, items):
    xml_info = write_objects(source_file, items)   
    return xml_info


def make_agent(premis,linkingEventIdentifier_value, agentId ):
    csv_file = os.path.expanduser("~/Desktop/premis_agents.csv")
    if os.path.isfile(csv_file):
        read_object = open(csv_file)
        reader = csv.reader(read_object)
        csv_list = list(reader)
        read_object.close()
    for lists in csv_list:
        for item in lists:
            if item == agentId:
                agent_info = lists
    agentIdType_value,agentIdValue_value,agentName_value,agentType_value, agentVersion_value,agentNote_value,agentRole = agent_info
    if agentVersion_value == 'ffmpeg_autoextract':
        agentVersion_value = subprocess.check_output(['ffmpeg','-version','-v','0']).splitlines()[0]
    premis_namespace            = "http://www.loc.gov/premis/v3"
    agent                       = ET.SubElement(premis, "{%s}agent" % (premis_namespace))
    premis.insert(-1, agent)
    agentIdentifier             = create_unit(1,agent,'agentIdentifier')
    agentIdType                 = create_unit(2,agentIdentifier,'agentIdentifierType')
    agentIdValue                = create_unit(2,agentIdentifier,'agentIdentifierValue')
    agentName                   = create_unit(2,agent,'agentName')
    agentType                   = create_unit(3,agent,'agentType')
    agentVersion                = create_unit(4,agent,'agentVersion')
    agentNote                   = create_unit(5,agent,'agentNote')
    linkingEventIdentifier      = create_unit(6,agent,'linkingEventIdentifier')
    agentIdType.text            = agentIdType_value
    agentIdValue.text           = agentIdValue_value
    agentName.text              = agentName_value
    agentType.text              = agentType_value
    agentVersion.text           = agentVersion_value
    agentNote.text              = agentNote_value
    linkingEventIdentifier.text = linkingEventIdentifier_value
    agent_info                  = [agentIdType_value,agentIdValue_value]
    return agent_info
    
def make_event(premis,event_type, event_detail, agentlist, eventID, eventLinkingObjectIdentifier):
        premis_namespace                    = "http://www.loc.gov/premis/v3"
        event = ET.SubElement(premis, "{%s}event" % (premis_namespace))
        premis.insert(-1,event)
        event_Identifier                    = create_unit(1,event,'event_Identifier')
        event_id_type                       = ET.Element("{%s}eventIdentifierType" % (premis_namespace))
        event_Identifier.insert(0,event_id_type)
        event_id_value                      = ET.Element("{%s}eventIdentifierValue" % (premis_namespace))
        event_Identifier.insert(0,event_id_value)
        event_Type                          = ET.Element("{%s}eventType" % (premis_namespace))
        event.insert(2,event_Type)
        event_DateTime                      = ET.Element("{%s}eventDateTime" % (premis_namespace))
        event.insert(3,event_DateTime)
        event_DateTime.text                 = time.strftime("%Y-%m-%dT%H:%M:%S")
        event_Type.text                     = event_type
        event_id_value.text                 = eventID
        event_id_type.text                  = 'UUID'
        eventDetailInformation              = create_unit(4,event,'event_DetailInformation')
        eventDetail                         = create_unit(0,eventDetailInformation,'eventDetail')
        eventDetail.text                    = event_detail
        linkingObjectIdentifier             = create_unit(5,event,'linkingObjectIdentifier')
        linkingObjectIdentifierType         = create_unit(0,linkingObjectIdentifier,'linkingObjectIdentifierType')
        linkingObjectIdentifierValue        = create_unit(1,linkingObjectIdentifier,'linkingObjectIdentifierValue')
        linkingObjectIdentifierValue.text   = eventLinkingObjectIdentifier
        linkingObjectRole                   = create_unit(2,linkingObjectIdentifier,'linkingObjectRole')
        linkingObjectIdentifierType.text    = 'UUID'
        linkingObjectRole.text              = 'source'
        for i in agentlist: 
            linkingAgentIdentifier              = create_unit(-1,event,'linkingAgentIdentifier')
            linkingAgentIdentifierType          = create_unit(0,linkingAgentIdentifier,'linkingAgentIdentifierType')
            linkingAgentIdentifierValue         = create_unit(1,linkingAgentIdentifier,'linkingAgentIdentifierValue')
            linkingAgentIdentifierRole          = create_unit(2,linkingAgentIdentifier,'linkingAgentRole')
            linkingAgentIdentifierRole.text     = 'implementer'
            linkingAgentIdentifierType.text     = i[0]
            linkingAgentIdentifierValue.text    = i[1]


def process_history(coding_dict, process_history_placement):
    process = create_revtmd_unit(process_history_placement, revtmd_capture_history, 'codingprocessHistory')
    counter1 = 1
    for i in OrderedDict(coding_dict):
        a = create_revtmd_unit(counter1, process, i)
        a.text = coding_dict[i]
        counter1 += 1
        
          
def main():
        source_file = sys.argv[1]
        items       = pg.main()
        xml_info    = make_premis(source_file, items)
        doc         = xml_info[0]
        premisxml   = xml_info[1]
        write_premis(doc, premisxml) 
           
def write_objects(source_file, items):

    manifest            = os.path.dirname(os.path.abspath(source_file)) + '/' + os.path.basename(source_file) + '_manifest.md5'
    premisxml           = os.path.dirname(os.path.dirname(source_file)) + '/metadata' '/' + os.path.basename(os.path.dirname(os.path.dirname(source_file))) + '_premis.xml'
    
    namespace           = '<premis:premis xmlns:premis="http://www.loc.gov/premis/v3" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:revtmd="http://nwtssite.nwts.nara/schema/" xsi:schemaLocation="http://www.loc.gov/premis/v3 https://www.loc.gov/standards/premis/premis.xsd http://nwtssite.nwts.nara/schema/  " version="3.0"></premis:premis>'
    premis_namespace    = "http://www.loc.gov/premis/v3"
    xsi_namespace       = "http://www.w3.org/2001/XMLSchema-instance"
    
    if os.path.isfile(premisxml):
        print 'looks like premis already exists?'
        parser      = ET.XMLParser(remove_blank_text=True)
        doc         = ET.parse(premisxml,parser=parser)
        premis      = doc.getroot()
        wav_uuid    = doc.findall('//ns:objectIdentifierValue',namespaces={'ns': "http://www.loc.gov/premis/v3"})[2]    
    else:
        premis              = ET.fromstring(namespace)
        doc                 = ET.ElementTree(premis)
    video_files         = get_input(source_file)
    mediainfo_counter   = 1
    # Assuming that directory input means image sequence...
    if video_files[0].endswith('wav'):
            premisxml           = os.path.dirname(os.path.dirname(source_file)) + '/metadata' + '/' + os.path.basename(os.path.dirname(os.path.dirname(source_file))) + '_premis.xml'
            print premisxml
            if os.path.isfile(premisxml):
                print 'looks like premis already exists?'
                parser      = ET.XMLParser(remove_blank_text=True)
                doc         = ET.parse(premisxml,parser=parser)
                premis      = doc.getroot()
                filetype    = 'audio'
                
            else:
                filetype = 'audio'
                root_uuid   = str(uuid.uuid4())
    else:
        filetype = 'image'
        object_parent = create_unit(0, premis, 'object')
        print 'first_object'
        object_identifier_parent                                = create_unit(1,object_parent, 'objectIdentifier')
        object_identifier_uuid                                  = create_unit(0,object_parent, 'objectIdentifier')
        object_identifier_uuid_type                             = create_unit(1,object_identifier_uuid, 'objectIdentifierType')
        object_identifier_uuid_type.text                        = 'UUID'
        object_identifier_uuid_value                            = create_unit(2,object_identifier_uuid, 'objectIdentifierValue') 
        representation_uuid                                     = str(uuid.uuid4())
        object_identifier_uuid_value.text = representation_uuid
        object_parent.insert(1,object_identifier_parent)
        ob_id_type                                              = ET.Element("{%s}objectIdentifierType" % (premis_namespace))
        ob_id_type.text                                         = 'IFI Irish Film Archive Object Entry Number'
        objectIdentifierValue                                   = create_unit(1, object_identifier_parent, 'objectIdentifierValue')
        objectIdentifierValue.text                              = items['oe']
        object_identifier_parent.insert(0,ob_id_type)  
        object_identifier_filmographic                          = create_unit(3,object_parent, 'objectIdentifier')
        object_identifier_filmographic_reference_number         = create_unit(1,object_identifier_filmographic, 'objectIdentifierType') 
        object_identifier_filmographic_reference_number.text    = 'IFI Irish Film Archive Filmographic Reference Number'
        object_identifier_filmographic_reference_value          = create_unit(2,object_identifier_filmographic, 'objectIdentifierValue') 
        object_identifier_filmographic_reference_value.text     = items['filmographic']
        objectCategory                                          = create_unit(4,object_parent, 'objectCategory')  
        objectCategory.text                                     = 'representation'
        relationship                                            = create_unit(4,object_parent, 'relationship')
        representationrelatedObjectIdentifierType               = create_unit(2,relationship, 'relatedObjectIdentifierType')
        representationrelatedObjectIdentifierValue              = create_unit(3,relationship,'relatedObjectIdentifierValue')
        relatedObjectSequence                                   = create_unit(4,relationship,'relatedObjectSequence')
        relatedObjectSequence.text                              = '1'
        relationshipType                                        = create_unit(0,relationship, 'relationshipType')
        relationshipType.text                                   = 'structural'
        relationshipSubType                                     = create_unit(1,relationship, 'relationshipSubType')
        relationshipSubType.text                                = 'has root'
        representationrelatedObjectIdentifierType.text          = 'UUID'
        if os.path.isfile(premisxml):
            wavrelationship                                            = create_unit(5,object_parent, 'relationship')
            wavRelatedObjectIdentifierType                          = create_unit(2,wavrelationship, 'relatedObjectIdentifierType')
            wavRelatedObjectIdentifierValue                         = create_unit(3,wavrelationship,'relatedObjectIdentifierValue')
            relationshipType                                        = create_unit(0,wavrelationship, 'relationshipType')
            relationshipType.text                                   = 'structural'
            relationshipSubType                                     = create_unit(1,wavrelationship, 'relationshipSubType')
            relationshipSubType.text                                = 'includes'
            wavRelatedObjectIdentifierType.text                     = 'UUID'
            wavRelatedObjectIdentifierValue.text                    = wav_uuid.text
        sourcerelationship                                            = create_unit(5,object_parent, 'relationship')
        sourceRelatedObjectIdentifierType                          = create_unit(2,sourcerelationship, 'relatedObjectIdentifierType')
        sourceRelatedObjectIdentifierValue                         = create_unit(3,sourcerelationship,'relatedObjectIdentifierValue')
        relationshipType                                        = create_unit(0,sourcerelationship, 'relationshipType')
        relationshipType.text                                   = 'derivation'
        relationshipSubType                                     = create_unit(1,sourcerelationship, 'relationshipSubType')
        relationshipSubType.text                                = 'has source'
        sourceRelatedObjectIdentifierType.text                     = 'IFI Irish Film Archive Accessions Register'
        sourceRelatedObjectIdentifierValue.text                    = items['sourceAccession']
        root_uuid                                               = str(uuid.uuid4())
        representationrelatedObjectIdentifierValue.text         = root_uuid
    rep_counter = 0
    for image in video_files:
        object_parent                                           = create_unit(mediainfo_counter,premis, 'object')
        object_identifier_parent                                = create_unit(1,object_parent, 'objectIdentifier')
        ob_id_type                                              = ET.Element("{%s}objectIdentifierType" % (premis_namespace))
        ob_id_type.text                                         = 'IFI Irish Film Archive Object Entry Number'
        object_identifier_parent.insert(0,ob_id_type)
        object_identifier_filmographic                          = create_unit(3,object_parent, 'objectIdentifier')
        object_identifier_filmographic_reference_number = create_unit(1,object_identifier_filmographic, 'objectIdentifierType') 
        object_identifier_filmographic_reference_number.text    = 'IFI Irish Film Archive Filmographic Reference Number'
        object_identifier_filmographic_reference_value          = create_unit(2,object_identifier_filmographic, 'objectIdentifierValue') 
        object_identifier_filmographic_reference_value.text     = items['filmographic']
        objectCategory                                          = ET.Element("{%s}objectCategory" % (premis_namespace))
        object_parent.insert(5,objectCategory)
        objectCategory.text                                     = 'file'
        objectCharacteristics                                   = create_unit(10,object_parent, 'objectCharacteristics')
        objectIdentifierValue                                   = create_unit(1, object_identifier_parent, 'objectIdentifierValue')
        objectIdentifierValue.text                              = items['oe']
        object_identifier_uuid                                  = create_unit(2,object_parent, 'objectIdentifier')
        object_identifier_uuid_type                             = create_unit(1,object_identifier_uuid, 'objectIdentifierType')
        object_identifier_uuid_type.text                        = 'UUID'
        object_identifier_uuid_value                            = create_unit(2,object_identifier_uuid, 'objectIdentifierValue') 
        file_uuid                                               = str(uuid.uuid4())
        if not filetype == 'audio':
            if rep_counter == 0:
                object_identifier_uuid_value.text = root_uuid
            else:
                object_identifier_uuid_value.text = file_uuid
        elif filetype == 'audio':
            object_identifier_uuid_value.text = root_uuid 
        rep_counter +=1
        format_ = ET.Element("{%s}format" % (premis_namespace))
        objectCharacteristics.insert(2,format_)
        
        mediainfo                       = subprocess.check_output(['mediainfo', '-f', '--language=raw', '--Output=XML', image])
        parser                          = ET.XMLParser(remove_blank_text=True)
        mediainfo_xml                   = ET.fromstring((mediainfo),parser=parser)
        fixity                          = create_unit(0,objectCharacteristics,'fixity')
        size                            = create_unit(1,objectCharacteristics,'size')
        size.text                       = str(os.path.getsize(image))
        formatDesignation               = create_unit(0,format_,'formatDesignation')
        formatName                      = create_unit(1,formatDesignation,'formatName')
        formatName.text                 = subprocess.check_output(['mediainfo', '--Inform=General;%InternetMediaType%', image]).rstrip()
        messageDigestAlgorithm          = create_unit(0,fixity, 'messageDigestAlgorithm')
        messageDigest                   = create_unit(1,fixity, 'messageDigest')
        objectCharacteristicsExtension  = create_unit(4,objectCharacteristics,'objectCharacteristicsExtension')
        objectCharacteristicsExtension.insert(mediainfo_counter, mediainfo_xml)
        if os.path.isdir(source_file):
            if not filetype == 'audio':
                relationship                        = create_unit(7,object_parent, 'relationship')
                relatedObjectIdentifierType         = create_unit(2,relationship, 'relatedObjectIdentifierType')
                relatedObjectIdentifierType.text    = 'UUID'
                relatedObjectIdentifierValue        = create_unit(3,relationship,'relatedObjectIdentifierValue')
                relatedObjectIdentifierValue.text   = representation_uuid
                relatedObjectSequence               = create_unit(4,relationship,'relatedObjectSequence')
                relatedObjectSequence.text          = str(mediainfo_counter)
                relationshipType                    = create_unit(0,relationship, 'relationshipType')
                relationshipType.text               = 'structural'
                relationshipSubType                 = create_unit(1,relationship, 'relationshipSubType')
                relationshipSubType.text            = 'is included in'
            messageDigestAlgorithm.text             = 'md5'

        md5_output                              = hashlib_md5(source_file, image, manifest)
        messageDigest.text                      = md5_output
        mediainfo_counter                       += 1
    # When the image info has been grabbed, add info about the representation to the wav file. This may be problematic if makedpx is run first..
    wav_object  = doc.findall('//ns:object',namespaces={'ns': "http://www.loc.gov/premis/v3"})[-1]
    if not filetype == 'audio':
        relationship                        = create_unit(8,wav_object, 'relationship')
        relatedObjectIdentifierType         = create_unit(2,relationship, 'relatedObjectIdentifierType')
        relatedObjectIdentifierType.text    = 'UUID'
        relatedObjectIdentifierValue        = create_unit(3,relationship,'relatedObjectIdentifierValue')
        relatedObjectIdentifierValue.text   = representation_uuid 
        relationshipType                    = create_unit(0,relationship, 'relationshipType')
        relationshipType.text               = 'structural'
        relationshipSubType                 = create_unit(1,relationship, 'relationshipSubType')
        relationshipSubType.text            = 'is included in'
    if filetype == 'audio':
        xml_info                                    = [doc, premisxml, root_uuid]
    else:    
        xml_info                                    = [doc, premisxml, representation_uuid]
    return xml_info
    
if __name__ == "__main__":
        main()

