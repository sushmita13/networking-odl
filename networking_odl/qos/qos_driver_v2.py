# Copyright (c) 2016 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from neutron.common import constants as n_consts
from neutron.services.qos.drivers import base
from neutron.services.qos import qos_consts
from neutron_lib.api.definitions import portbindings
from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from networking_odl.common import constants as odl_const
from networking_odl.journal import journal
from networking_odl.qos import qos_utils

LOG = logging.getLogger(__name__)

# TODO(manjeets) fetch these from Neutron NB
# Only bandwidth limit is supported so far.
SUPPORTED_RULES = {
    qos_consts.RULE_TYPE_BANDWIDTH_LIMIT: {
        qos_consts.MAX_KBPS: {
            'type:range': [0, n_consts.DB_INTEGER_MAX_VALUE]},
        qos_consts.MAX_BURST: {
            'type:range': [0, n_consts.DB_INTEGER_MAX_VALUE]},
        qos_consts.DIRECTION: {
            'type:values': [n_consts.EGRESS_DIRECTION]}
    },
}
VIF_TYPES = [portbindings.VIF_TYPE_OVS, portbindings.VIF_TYPE_VHOST_USER]
VNIC_TYPES = [portbindings.VNIC_NORMAL]


class OpenDaylightQosDriver(base.DriverBase):

    """OpenDaylight QOS Driver

    This code is backend implementation for Opendaylight Qos
    driver for Openstack Neutron.
    """

    @staticmethod
    def create():
        return OpenDaylightQosDriver()

    def __init__(self, name='OpenDaylightQosDriver',
                 vif_types=VIF_TYPES,
                 vnic_types=VNIC_TYPES,
                 supported_rules=SUPPORTED_RULES,
                 requires_rpc_notifications=False):
        super(OpenDaylightQosDriver, self).__init__(
            name, vif_types, vnic_types, supported_rules,
            requires_rpc_notifications)
        LOG.debug("Initializing OpenDaylight Qos driver")
        self.journal = journal.OpendaylightJournalThread()

    def _record_in_journal(self, context, op_const, qos_policy):
        data = qos_utils.convert_rules_format(qos_policy.to_dict())
        journal.record(context, odl_const.ODL_QOS_POLICY,
                       data['id'], op_const, data)

        self.journal.set_sync_event()

    # TODO(manjeets) QoS interface does not have precommit
    # and postcommit mechanism for now, Revisit this driver
    # once interface is fixed and separate record in journal
    # and sync event to precommit and postcommit.
    # https://review.openstack.org/#/c/421818/

    @log_helpers.log_method_call
    def create_policy(self, context, qos_policy):
        self._record_in_journal(context, odl_const.ODL_CREATE, qos_policy)

    @log_helpers.log_method_call
    def update_policy(self, context, qos_policy):
        self._record_in_journal(context, odl_const.ODL_UPDATE, qos_policy)

    @log_helpers.log_method_call
    def delete_policy(self, context, qos_policy):
        self._record_in_journal(context, odl_const.ODL_DELETE, qos_policy)
