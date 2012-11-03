from io import BytesIO
from lxml import etree
from route53.util import prettyprint_xml

def write_change(change):
    """
    Creates an XML element for the change.

    :param change_set.ChangeSet change_set: The ChangeSet object to create the
        XML doc from.

    :rtype: lxml.etree._Element
    :returns: A fully baked Change tag.
    """

    action, rrset = change

    e_change = etree.Element("Change")

    e_action = etree.SubElement(e_change, "Action")
    e_action.text = action

    e_rrset = etree.SubElement(e_change, "ResourceRecordSet")

    e_name = etree.SubElement(e_rrset, "Name")
    e_name.text = rrset.name

    e_type = etree.SubElement(e_rrset, "Type")
    e_type.text = rrset.rrset_type

    e_ttl = etree.SubElement(e_rrset, "TTL")
    e_ttl.text = str(rrset.ttl)


    if rrset.is_alias_record_set():
        # A record sets in Alias mode don't have any resource records.
        return e_change

    e_resource_records = etree.SubElement(e_rrset, "ResourceRecords")

    for value in rrset.records:

        e_resource_record = etree.SubElement(e_resource_records, "ResourceRecord")
        e_value = etree.SubElement(e_resource_record, "Value")
        e_value.text = value

    return e_change

def change_resource_record_set_writer(connection, change_set, comment=None):
    """
    Forms an XML string that we'll send to Route53 in order to change
    record sets.

    :param Route53Connection connection: The connection instance used to
        query the API.
    :param change_set.ChangeSet change_set: The ChangeSet object to create the
        XML doc from.
    :keyword str comment: An optional comment to go along with the request.
    """

    e_root = etree.Element(
        "ChangeResourceRecordSetsRequest",
        xmlns=connection.xml_namespace
    )

    e_change_batch = etree.SubElement(e_root, "ChangeBatch")

    if comment:
        e_comment = etree.SubElement(e_change_batch, "Comment")
        e_comment.text = comment

    e_changes = etree.SubElement(e_change_batch, "Changes")

    for change in change_set.changes:
        e_changes.append(write_change(change))

    e_tree = etree.ElementTree(element=e_root)

    print(prettyprint_xml(e_root))

    fobj = BytesIO()
    # This writes bytes.
    e_tree.write(fobj, xml_declaration=True, encoding='utf-8', method="xml")
    return fobj.getvalue().decode('utf-8')