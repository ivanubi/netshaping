from net import Connection
router = Connection('192.168.18.117', username = 'jania', password = 'cisco', device_type = 'cisco_ios')
router.set_hostname('HELLO')

router = Netmiko(host = '192.168.18.117', username = 'jania', password = 'cisco', device_type = 'cisco_ios')

