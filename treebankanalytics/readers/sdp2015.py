from treebankanalytics.readers import sdp_utils 

__all__ = ['sdp2015_reader']

def sdp2015_reader(fileo):
    for g in sdp_utils.common_sdp_reader(fileo, '2015'):
        yield g
