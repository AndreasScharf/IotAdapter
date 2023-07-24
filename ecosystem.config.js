module.exports = {
  apps: [{
    name: "iot",
    script: "/home/pi/Documents/IotAdapter/iotadapter.py",
    interpreter: 'python3',
    out_file: "/dev/null",
    error_file: "/dev/null",
  }
  ]
}