import json
import requests
import os
from pyCGA.opencgarestclients import OpenCGAClient
# make a cip api client
from pycipapi.cipapi_client import CipApiClient

c = CipApiClient(url_base='https://cipapi-gms-test.gel.zone/', user=' ', password=' ')
configuration_test = {
    "version": "v1",
    "rest": {
        "hosts": [
            "https://bio-test-opencgainternal.gel.zone/opencga"
        ]
    }
}
oc = OpenCGAClient(configuration=configuration_test, user=' ', pwd=' ')

listOfCases = ['433-1']
def get_case(listOfCases):
    CaseList = []
    for caseid in listOfCases:
        id, version = caseid.split('-')
        case = c.get_case(case_id=id, case_version=version, reports_v6='true',)
        CaseList.append(case)
    return CaseList


def get_cnv_vcf_paths(samples, study, cohort):
    cnv_vcf_uris = []
    for sample in samples:
        VCF_uris = oc.files.search(study=study, samples=sample, format='VCF',
                                       cohort=cohort, include='uri').get()
        for uri in VCF_uris:
            if uri['uri'].endswith("cnv.vcf.gz"):
                cnv_vcf_uris.append({
                  "fileType": "VCF_SV_CNV",
                  "md5Sum": None,
                  "sampleId": [sample],
                  "uriFile": uri['uri'].split('//')[1]
                })
    return cnv_vcf_uris

def add_cnv_vcfs(IR, cnv_vcf_uris):
    vcfs = IR['vcfs']    
    for cnv_vcf_uri in cnv_vcf_uris:
        if cnv_vcf_uri not in vcfs:
            vcfs.append(cnv_vcf_uris)
    IR['vcfs'] = vcfs
    return IR


Caselist = get_case(listOfCases)

for case in Caselist:
    IR = case.interpretation_request_data['json_request']
    last_status = case.last_status
    samples = case.samples
    cnv_vcf_uris = get_cnv_vcf_paths(samples=samples, study="RD38GMSE2E", cohort=IR['familyInternalId'])
    # print(cnv_vcf_uris)
    updatedIR = add_cnv_vcfs(IR, cnv_vcf_uris)
    print(IR['vcfs'])
    if last_status == 'blocked':
        Q = input("This is a blocked case. Would you like to continue modifying the case? (y/n)")
        if Q != 'y' or 'yes':
            continue

    case.submit_interpretation_request(cip_api_client=c, payload=updatedIR, reports_v6='true',
                                       extra_fields={}, force=True)
    c.patch(c.build_url(c.url_base, c.IR_ENDPOINT, case.interpretation_request_id, case.version,
                        'request-status/'), payload={'status': last_status})
