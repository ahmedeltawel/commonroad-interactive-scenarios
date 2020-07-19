from xml.etree import ElementTree

def rou_file_determinism_check(rou_file: str) -> bool:

    #read rou.xml file
    tree = ElementTree.parse(rou_file)
    root = tree.getroot()
    
    #get all parameters that can be set to 'random' and effect the determinism
    list_departSpeed = []
    list_departPos = []
    list_departLane = []
    
    vehicles = root.findall('vehicle')
    deterministic = True
    
    if vehicles:
        for vehicle in vehicles:
            #get the list of 'departSpeed' for all vehicles
            list_departSpeed.append(vehicle.get('departSpeed'))
            #get the list of 'departPos' for all vehicles
            list_departPos.append(vehicle.get('departPos'))
            #get the list of 'departLane' for all vehicles
            list_departLane.append(vehicle.get('departLane'))
        #check if any item in the lists is set to 'random'
        list_param = list_departSpeed + list_departPos + list_departLane
        for param in list_param:
            if param == 'random':
                deterministic = False
                print("Found parameters set to 'random'.")
                continue
    else:
        deterministic = False
        print("There is no vehicle.")
    return deterministic
    
        
 


        