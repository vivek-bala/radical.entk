from prof_utils import get_profiles
from pprint import pprint

if __name__ == '__main__':

    prof, acc, hostmap = get_profiles(src='./sleep-250')

    pprint (prof)