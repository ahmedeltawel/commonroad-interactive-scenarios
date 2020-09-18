from xml.etree import ElementTree


def rou_file_determinism_check(rou_file: str) -> bool:
    """
    This function gathers info from route files and checks if there are any settings,
    which can let vehicles spawn randomly.
    """

    # Read rou.xml file
    tree = ElementTree.parse(rou_file)
    root = tree.getroot()
    
    deterministic = True
    
    vehicles = root.findall('vehicle')
    flows = root.findall('flow')
    trips = root.findall('trip')

    all_elements = vehicles + flows + trips

    # Check if there exist flows with a random number of vehicles
    random_flows = [flow for flow in flows if flow.get('probability') is not None]
    if len(random_flows) != 0:
        deterministic = False
        print(f"Found flows with random number of vehicles: {random_flows}.")

    # Check if there exists random attributes
    attribute_types = ['departSpeed', 'departPos', 'departLane', 'arrivalPos']
    list_random_params = [f"{element}.{attribute_tpye}"
                          for element in all_elements
                          for attribute_tpye in attribute_types
                          if element.get(attribute_tpye) == 'random']
    if len(list_random_params) != 0:
        deterministic = False
        print(f"Found parameters set to 'random': {list_random_params}.")
            
    # Check if there exists route distributions
    list_route_dist = root.findall('routeDistribution')
    if len(list_route_dist) != 0:
        deterministic = False
        print(f"Found route distribution: {list_route_dist}")

    # Check if there exists vehicle type distributions
    list_vType_dist = root.findall('vTypeDistribution')
    if len(list_vType_dist) != 0:
        deterministic = False
        print(f"Found vehicle type distribution: {list_vType_dist}")

    # Check if there exists speed distributions or stochastic car-following described in 'vType'
    vType_elements = root.findall('vType')

    list_random_speedFactor = [vType for vType in vType_elements if "norm" in vType.get('speedFactor')]
    if len(list_random_speedFactor) != 0:
        deterministic = False
        print(f"Found random speed factor: {list_random_speedFactor}.")

    list_random_speedDev = [vType for vType in vType_elements if vType.get('speedDev') != "0"]
    if len(list_random_speedDev) != 0:
        deterministic = False
        print(f"Found random speed deviation: {list_random_speedDev}.")

    list_random_sigma = [vType for vType in vType_elements if vType.get('sigma') != "0"]
    if len(list_random_sigma) != 0:
        deterministic = False
        print(f"Found car following stochastic behaviour: {list_random_sigma}.")
        
    return deterministic
