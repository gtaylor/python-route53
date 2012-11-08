import uuid
from io import BytesIO
from lxml import etree

def create_hosted_zone_writer(connection, name, caller_reference, comment):
    """
    Forms an XML string that we'll send to Route53 in order to create
    a new hosted zone.

    :param Route53Connection connection: The connection instance used to
        query the API.
    :param str name: The name of the hosted zone to create.
    """

    if not caller_reference:
        caller_reference = str(uuid.uuid4())

    e_root = etree.Element(
        "CreateHostedZoneRequest",
        xmlns=connection._xml_namespace
    )

    e_name = etree.SubElement(e_root, "Name")
    e_name.text = name

    e_caller_reference = etree.SubElement(e_root, "CallerReference")
    e_caller_reference.text = caller_reference

    if comment:
        e_config = etree.SubElement(e_root, "HostedZoneConfig")
        e_comment = etree.SubElement(e_config, "Comment")
        e_comment.text = comment

    e_tree = etree.ElementTree(element=e_root)

    fobj = BytesIO()
    # This writes bytes.
    e_tree.write(fobj, xml_declaration=True, encoding='utf-8', method="xml")
    return fobj.getvalue().decode('utf-8')