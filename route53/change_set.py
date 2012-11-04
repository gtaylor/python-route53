from route53.exceptions import Route53Error

class ChangeSet(object):
    """
    These objects are used behind-the-scenes to change ResourceRecordSets
    via the Route53 API.
    """

    def __init__(self, connection, hosted_zone_id):
        """
        :param Route53Connection connection: The connection instance being
            used to send the change request.
        :param str hosted_zone_id: The ID of the hosted zone this change set
            pertains to.
        """

        self.connection = connection
        self.hosted_zone_id = hosted_zone_id
        self.creations = []
        self.deletions = []

    def add_change(self, action, record_set):
        """
        Adds a change to this change set.

        :param str action: Must be one of either 'CREATE' or 'DELETE'.
        :param resource_record_set.ResourceRecordSet record_set: The
            ResourceRecordSet object that was created or deleted.
        """

        action = action.upper()

        if action not in ['CREATE', 'DELETE']:
            raise Route53Error("action must be one of 'CREATE' or 'DELETE'")

        change_tuple = (action, record_set)

        if action == 'CREATE':
            self.creations.append(change_tuple)
        else:
            self.deletions.append(change_tuple)