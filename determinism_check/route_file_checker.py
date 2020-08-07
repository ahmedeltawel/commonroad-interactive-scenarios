from xml.etree import ElementTree

def rou_file_determinism_check(rou_file: str) -> bool:
    '''
    This function gathers info from route files and checks if there are any settings, which can let vehicles spawn randomly.
    '''

    #read rou.xml file
    tree = ElementTree.parse(rou_file)
    root = tree.getroot()
    
    deterministic = True
    
    vehicles = root.findall('vehicle')
    flows = root.findall('flow')
    trips = root.findall('trip')
    
    
    #get lists of parameters that can be set to 'random' and effect the determinism
    if deterministic:
        list_departSpeed = []
        list_departPos = []
        list_departLane = []
        list_arrivalPos = []
        
        all_attributes = vehicles + flows + trips
        if all_attributes:
            for attribute in all_attributes:
                #get the list of 'departSpeed' for all vehicles, flows and trips
                list_departSpeed.append(attribute.get('departSpeed'))
                #get the list of 'departPos' for all vehicles, flows and trips
                list_departPos.append(attribute.get('departPos'))
                #get the list of 'departLane' for all vehicles, flows and trips
                list_departLane.append(attribute.get('departLane'))
                #get the list of 'arrivalPos' for all vehicles, flows and trips
                list_departLane.append(attribute.get('arrivalPos'))
                
            #check if any item in the lists is set to 'random'
            list_param = list_departSpeed + list_departPos + list_departLane + list_arrivalPos
            for param in list_param:
                if param == 'random':
                    deterministic = False
                    print("Found parameters set to 'random'.")
                    break
        else:
            deterministic = False
            print("There is no vehicle, flow or trip defined.")
            
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
    #check if there exists speed distributions or stochastic car-following described in 'vType'
    if deterministic:
        list_speedFactor = []
        list_speedDev = []
        list_sigma = []
        vTypes = root.findall('vType')
        for vType in vTypes:
            list_speedFactor.append(vType.get('speedFactor'))
            list_speedDev.append(vType.get('speedDev'))
            list_sigma.append(vType.get('sigma'))
        for item in range(len(list_speedDev)):
            if not list_speedDev[item] == "0":
                print("Found speed deviation.")
                deterministic = False
                break
            if "norm" in list_speedFactor[item]:
                print("Found speed deviation.")
                deterministic = False
                break
            if not list_sigma[item] == "0":
                print("Found stochastic car following behaviors.")
                deterministic = False
                break
    #check if there exist flows with a random number of vehicles
    if deterministic:
        for flow in flows:
            if flow.get('probability'):
                print("Found flows with random number of vehicles")
                break
        
    return deterministic
    
        
 


        