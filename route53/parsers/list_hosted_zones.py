from lxml import etree
from route53.util import prettyprint_xml

def list_hosted_zones_parser(xml_str):
    root = etree.fromstring(xml_str)
    print(prettyprint_xml(root))
    print(root)

    if not 'ListHostedZonesResponse' in root.tag:
        # TODO: Error condition.
        raise Exception("Something bad happened!")

    is_truncated = root.find('./{*}IsTruncated').text == 'true'

    for child in root:
        print(child.tag)

    if not is_truncated:
        return



    return xml_str
