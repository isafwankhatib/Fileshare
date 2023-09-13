"""
Copyright .. Larsen & Toubro Infotech Ltd.
Version : 1.0
Description : This is file for class of methods with
rules defined as per Client.
File Name : conditions_client_specific.py
Date : 30/09/2021
"""

import sys
import pandas as pd

from configs import LOGGER, CONFIG
from libs.conditions.ticketing_conditions import TicketingConditions
from utils.utils import exception_logger, switcher



class ClientSpecificCutomRules(TicketingConditions):

    _instance = None

    def __new__(cls):
        """
        CustomRules singleton method

        Init Method to allow the class to initialize the attributes.
        Also other attributes like objects of other classes and initializing
        configurations defined in the DB and ORM object.

        Parameters: None

        Returns: None

        """
        if not cls._instance:
            cls._instance = super(ClientSpecificCutomRules, cls).__new__(cls)
        return cls._instance

    def conditions_client_customized(self, data, consumer, extra_header):
        src_sapsolman = 'SAP SOLUTION MANAGER 7.2'
        src_ibm = 'CCDev'
        src_splunk = 'Splunk'
        """
        conditions_client_customized method

        This Function has business rules defined as per the client.
        The rules will be executed on the input data and relevant actions
        will be triggered.
        This will be a sequential evaluation.

        Parameters:
        data (json) : Input Data on which the rules will be evaluated
        consumer(object) :  Kafka consumer object

        Returns:
        string : Response based on the evaluation of rules.

                Values coming in payload of Rule Engine Kafka Topic for SAPSOLMAN:-
                child_source =   source
                child_ci_name    =   cmdb_ci

                Values Configured in Alerts_template_tbl :-

                cmdb_ci =cmdb_ci

                Values coming in payload of Rule Engine Kafka Topic for Splunk:

                child_source =   result_source
                child_ci_name    =  result_cmdb_ci
                child_short_description = result_error_type


                Values Configured in Alerts_template_tbl :-

                cmdb_ci =cmdb_ci
                alert_type = result_error_type

                Values coming in payload of Rule Engine Kafka Topic for IBM:

                child_source =   ccName
                child_ci_name    =  nodeId
                child_short_description = actionId


                Values Configured in Alerts_template_tbl :-

                cmdb_ci = nodeId
                alert_type = actionId
        """
        return_val = "break"
        try:
            LOGGER.info("Client specific code needs to be added in this!!",
                        extra=extra_header)
            data = self.alert_switcher(data)
            incident_id = self.check_duplicate(data['coalesce_sd'], extra_header)
            if incident_id:
                return_val = self.duplicate_alert_processing(incident_id, data,
                                                             extra_header)
                LOGGER.info("Duplicate Alerts",extra=extra_header)
            elif data['child_alert_state'].lower() == 'down':
                template_df = self.custom_rule.final_df
                ticket_data_df = pd.DataFrame([], columns=[])
                #SAPSOLMAN rules starts here
                #It will print incoming alert data
                LOGGER.info("alert_data:{}".format(data),extra=extra_header)
                if data['child_source'].lower() == src_sapsolman.lower():
                    ticket_data_df = template_df[(template_df['cmdb_ci'] == data['child_ci_name']) & (template_df['custom_1'] == data['child_custom4'])]
                    LOGGER.info("ticket_data_df:{}".format(ticket_data_df),extra=extra_header)
                    LOGGER.info("Conditions passed for SAP SOLMAN ... Going ahead with ticket creation",extra=extra_header)
                #SAPSOLMAN rules ends here
                #IBM rules start here
                #LOGGER.info("Printing SRC IBM VALUE %s",src_ibm,extra=extra_header)
                elif data['child_source'].lower() == src_ibm.lower():
                      ticket_data_df = template_df[(template_df['alert_type'] == data['child_short_description'])]
                      LOGGER.info("Conditions passed for IBM CC ... Going ahead with ticket creation",extra=extra_header)
                #IBM ENDS HERE
                #Splunk rules START HERE
                elif data['child_source'].lower() == src_splunk.lower():
                     if data['child_ci_name'] in ('uat-sa-sfdc-sa0014-v1','uat-sa-sap-na-sa0008-v1','uat-sa-kinvey-power-house-sa0020-v1','uat-sa-kinvey-power-route-sa0021-v1','uat-sa-workday-sa0001-v1','uat-pi-workers-pi0001-v1','uat-pi-pay-rates-pi0004-v1','uat-pi-locations-pi0002-v1','uat-pi-blood-lead-pi0008-v1'):
                         ticket_data_df = template_df[(template_df['alert_type'] == data['child_short_description']) & (template_df['cmdb_ci'] == data['child_ci_name'])]
                     elif data['child_ci_name'] in ('pi-workers-pi0001-v1','BES MFG/Pro USCAN','GE MES Proficy GLBL','BZVWINSR11','B0729S006','B2335s041','b0621s129','b0621s171','b2326s021','B2443s033','B0569S13','B0567S13','B4666S51'):
                         ticket_data_df = template_df[(template_df['alert_type'] == data['child_short_description']) & (template_df['cmdb_ci'] == data['child_ci_name']) & (template_df['custom_1'] == data['child_custom5'])]
                         LOGGER.info("Conditions 1 passed for SPLUNK... Going ahead with ticket creation",extra=extra_header)
                     elif data['child_custom5'] in ('C0095','C0096'):
                         ticket_data_df = template_df[(template_df['custom_1'] == data['child_custom5'])]
                         LOGGER.info("Condition 2 passed for SPLUNK..Going ahead with creation",extra=extra_header)
                     elif data['child_short_description'] in ('AMQ critical threshold alert','CPU usage alert','Memory usage alert','Worker unresponsive alert'):
                         ticket_data_df = template_df[(template_df['alert_type'] == data['child_short_description'])]
                         LOGGER.info("Condition 3 passed for SPLUNK..Going ahead with creation",extra=extra_header)
                #Splunk rules ends here
                return_val = self.templatize_processing(ticket_data_df, data, extra_header)
            else:
                LOGGER.info("Ignoring the alert as it is neither Duplicate nor Down.",
                            extra=extra_header)
        except Exception as exc_msg:
            consumer.commit()
            LOGGER.error(exc_msg, extra=extra_header)
            exception_logger(sys.exc_info(), extra_header)
        return return_val

    @staticmethod
    def generate_work_notes(alert_data):
        """
        Method to create work notes for Update ticket
        :param: Alert Data
        :return: Formatted Work Notes for an Incident
        """
        return "SOURCE: " + alert_data['child_source'] + " \nIMPACTED CI: " + alert_data[\
               'child_ci_name'] + " \n STATUS: " + alert_data[\
               'child_alert_state'] + " \n DESCRIPTION: " + alert_data['child_description']\
               + " \n CUSTOM MODIFIED"
