from prof_utils import get_profile, get_description
from pprint import pprint

if __name__ == '__main__':

    prof, acc, hostmap = get_profile(src='./sleep-250')

    pprint (prof)

    #json  = get_description(src='./')