from xml.etree import ElementTree

def rou_file_determinism_check(rou_file: str) -> bool:
    '''
    This function gathers info from route files and checks if there are any settings, which can let vehicles spawn randomly.
    '''

    #read rou.xml file
    tree = ElementTree.parse(rou_file)
    root = tree.getroot()
    
    deterministic = True
    
    #get lists of parameters that can be set to 'random' and effect the determinism
    if deterministic:
        list_departSpeed = []
        list_departPos = []
        list_departLane = []
        list_arrivalPos = []

        vehicles = root.findall('vehicle')
        if vehicles:
            for vehicle in vehicles:
                #get the list of 'departSpeed' for all vehicles
                list_departSpeed.append(vehicle.get('departSpeed'))
                #get the list of 'departPos' for all vehicles
                list_departPos.append(vehicle.get('departPos'))
                #get the list of 'departLane' for all vehicles
                list_departLane.append(vehicle.get('departLane'))
                #get the list of 'arrivalPos' for all vehicles
                list_departLane.append(vehicle.get('arrivalPos'))
                
            #check if any item in the lists is set to 'random'
            list_param = list_departSpeed + list_departPos + list_departLane + list_arrivalPos
            for param in list_param:
                if param == 'random':
                    deterministic = False
                    print("Found parameters set to 'random'.")
                    break
        else:
            deterministic = False
            print("There is no vehicle.")
            
    #check if there exists route distributions
    if deterministic:
        route_dist = root.findall('routeDistribution')
        if route_dist:
            print("Found route distribution.")
            deterministic = False
    #check if there exists vehicle type distributions
    if deterministic:
        vType_dist = root.findall('vTypeDistribution')
        if vType_dist:
            print("Found vehicle type distribution.")
            deterministic = False
    #check if there exists speed distributions
    if deterministic:
        list_speedFactor = []
        list_speedDev = []
        vTypes = root.findall('vType')
        for vType in vTypes:
            list_speedFactor.append(vType.get('speedFactor'))
            list_speedDev.append(vType.get('speedDev'))
        for speedDev in list_speedDev:
            if not speedDev == "0":
                print("Found speed deviation.")
                deterministic = False
                break
        for speedFactor in list_speedFactor:
            if "norm" in speedFactor:
                print("Found speed deviation.")
                deterministic = False
                break
    return deterministic
    
        
 


        