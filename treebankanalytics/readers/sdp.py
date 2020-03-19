from treebankanalytics.readers import sdp_utils 

__all__ = ['sdp_reader']

def sdp_reader(fileo):
    for g in sdp_utils.common_sdp_reader(fileo, '2014'):
        yield g
