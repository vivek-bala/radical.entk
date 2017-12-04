__copyright__   = "Copyright 2017-2018, http://radical.rutgers.edu"
__author__      = "Vivek Balasubramanian <vivek.balasubramanian@rutgers.edu>"
__license__     = "MIT"

# -----------------------------------------------------------------------------
# common states - Pipeline, Stage, Task
INITIAL         = 'DESCRIBED'
SCHEDULING      = 'SCHEDULING'

# common states - Stage, Task
SCHEDULED       = 'SCHEDULED'

# unique states - Tasks
SUBMITTING      = 'SUBMITTING'
SUBMITTED       = 'SUBMITTED'
COMPLETED       = 'EXECUTED'
DEQUEUEING      = 'DEQUEUEING'
DEQUEUED        = 'DEQUEUED'        


# common states - Pipeline, Stage, Task
DONE            = 'DONE'
FAILED          = 'FAILED'
TERMINATED      = 'TERMINATED'

# common states - Pipeline, Stage
SKIPPED         = 'SKIPPED'

# shortcut
FINAL = [DONE, FAILED, TERMINATED]


## Assign numeric values to states
state_numbers = {
    
    INITIAL         : 1,
    SCHEDULING      : 2,
    SCHEDULED       : 3,
    SUBMITTING      : 4,
    SUBMITTED       : 5,
    COMPLETED       : 6,
    DEQUEUEING      : 7,
    DEQUEUED        : 8,
    DONE            : 9,
    FAILED          : 9,
    TERMINATED      : 9,
    SKIPPED         : 10
}

## Get back string values from numeric values for states
state_strings = {}
for k,v in state_numbers.iteritems():
    state_strings[v] = k