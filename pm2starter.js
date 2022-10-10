module.exports = {
  apps : [{
    name   : "iot",
    script : "/home/pi/Documents/IotAdapter/iotadapter.py",
    interpreter: '/usr/local/bin/python3.8',
    out_file: "/dev/null",
    error_file: "/dev/null",
  },
    {
      name: "web",
      script: "/home/pi/Documents/IotAdapter/webserver/index.js",
      out_file: "/dev/null",
      error_file: "/dev/null",
    }
  ]
}