const express = require('express');
const app = express();
const http = require('http').Server(app);
const io = require('socket.io')(http);
const fs = require('fs');
const axios = require('axios');
const bcrypt = require('bcryptjs');

let assert = require('assert');
let pythonBridge = require('python-bridge');
const USERS_PATH = __dirname + '/users.json';
const CONFIG_PATH = __dirname +  '/../config.json'


const VORGEGEBENE_JSON = {
  "ip":"85.214.215.187",
  "port": 5000,
  "data": []
}

app.use(express.static(__dirname +  '/client'));
app.get('*', (req, res)=>{
    res.sendFile(__dirname + '/client/index.html');
});
io.on('connection', function(socket){
  socket.on('login', (data)=>{
    console.log('data', data);
    let username = data.email;
    let password = data.password;

    axios({
      method: 'post',
      url: 'https://license.enwatmon.de/login',
      data: data
        }).then(response =>{
          console.log(response.data)
          if(!response.data.token)
            socket.emit('login_failed', '')
          else{
            socket.emit('login_success', {token:response.data.token});
            bcrypt.hash(password, 10, function(err, result) {
              let data = JSON.stringify({email: username, password: result, token:response.data.token});
              fs.writeFileSync(USERS_PATH, data);
            });
          }


        }).catch( (e) =>{
          fs.readFile(USERS_PATH, (err, data) => {
            if (err){
              socket.emit('login_success', {token: 12345})
              return
            }
            let users = JSON.parse(data);
            if(users.email == username){
              bcrypt.compare(password, users.password, function(err, result) {
                if(result)
                  socket.emit('login_success', {token: users.token})
                else
                  socket.emit('login_failed', '')
              });
            }else {
              socket.emit('login_failed', '')
            }
          });
      });

  });
  socket.on('set_Table', (data)=>{
    console.log('change table to', data);
    let python = pythonBridge()
    python.ex`
    import snap7
    from snap7.util import *
    from snap7.snap7types import *

    def checkRequest(ip, db, offset, length, datatype):

      s7 = snap7.client.Client()

      try:
        s7.connect(ip, 0, 1)
      except:
        return 'NoConnect'

      print(ip, s7.get_connected())

      data = 0

      try:
        data = s7.db_read(int(db), int(offset), int(length))
      except:
        return 'OutofRange'

      byte_index = int((float(offset) - int(offset)) * 10)
      value = 0.0
      s7.disconnect()
      if datatype=='bit':
        return get_bool(data, byte_index, 0)
      elif datatype=='word' or datatype=='byte':
        return get_int(data, 0)
      elif datatype=='dint':
        return get_dint(data, 0)
      elif datatype=='real':
       return get_real(data, 0)
      else:
        return -1

    `
    const data_table = [];
    let menge = data.table.filter(item => !(item.type != 'S7' || item.ip == '' || item.db == '' || item.datatype == '' || !item.active)).length;
    let res_index = 0;
    for (var line of data.table) {
      if (line.type != 'S7' || line.ip == '' || line.db == '' || line.datatype == '' || !line.active)
        continue
      python`checkRequest(${line.ip},${line.db} , ${line.offset} , 4, ${line.datatype})`.then(x => {

        console.log(x)
        if (x == 'NoConnect' || x == 'OutofRange') {
          socket.emit('s7Error', {Error: 'NoConnect'})
          data.table[res_index].active = false;

        }
        else {
          data.table[res_index].active = true;
          data_table.push(data.table[res_index])
        }
        res_index++;
        if(menge <= res_index){
          VORGEGEBENE_JSON.data = data_table;
          let mad_item = data_table.find(elem => elem.name == 'MAD')
          VORGEGEBENE_JSON.mad = mad_item? mad_item.value: '';
          let data = JSON.stringify(VORGEGEBENE_JSON);
          fs.writeFileSync(CONFIG_PATH, data);
          console.log('table_change success');
        }
      });

    }
    python.end();
  });
  socket.on('get_Table', ()=>{
    fs.readFile(CONFIG_PATH, (err, data) => {
      if(err){
        let data = JSON.stringify(VORGEGEBENE_JSON);
        fs.writeFileSync(CONFIG_PATH, data);
        socket.emit('get_Table_back',{table: [] });
        return
      }

      let config = JSON.parse(data);
      console.log(config);
      socket.emit('get_Table_back',{table: config.data });
    });
  })
});

http.listen(8000, ()=>{
  console.log('listening on *:8000');
});
