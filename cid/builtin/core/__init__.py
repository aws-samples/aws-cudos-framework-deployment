# This plugin implements TAO dashboard

def onInit(cxt):
    # STS context, extract user session -> detect Bubblewand
    cxt.defaultAthenaDataSource = 'defaultDS'
    cxt.defaultAthenaDatabase = 'defaultDS'
    cxt.defaultAthenaTable = 'defaultDS'
    pass
