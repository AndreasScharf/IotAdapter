const express = require('express');
const app = express();
const http = require('http').Server(app);
const io = require('socket.io')(http);
const fs = require('fs');
const axios = require('axios');
const bcrypt = require('bcryptjs');

let pythonBridge = require('python-bridge');
const USERS_PATH = './users.json';
const CONFIG_PATH = '../config.json'


const VORGEGEBENE_JSON = {
  "ip":"85.214.215.187",
  "port": 5000,
  "data": []
}

app.use(express.static('client'));
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
            console.log('letzs hash');
            bcrypt.hash(password, 10, function(err, result) {
              if (err)
                console.log(err);
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
    console.log('save with out test');
    VORGEGEBENE_JSON.data = data_table;
    for (var line of data_table) {
      if (line.type == 'static' & &( line.type == 'MAD' ||  line.type == 'mad')) {
          VORGEGEBENE_JSON.mad = line.value;
      }
    }

    let data_to_write = JSON.stringify(VORGEGEBENE_JSON);
    fs.writeFileSync(CONFIG_PATH, data_to_write);

    /*
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
    let menge = data.table.length;
    let res_index = 0;
    for (var line of data.table) {
      if (line.type != 's7' || line.ip == '' || line.db == '' || line.datatype == '' || !line.active){
        line.active = true;
        data_table.push(line)
        res_index++;
        continue
      }else {
        python`checkRequest(${line.ip}, ${line.db} , ${line.offset} , 4, ${line.datatype})`.then(x => {
          console.log('line', data.table[res_index]);
          if ((x == 'NoConnect' || x == 'OutofRange') && data.table[res_index].type == 's7') {
            console.log(x);
            data.table[res_index].active = false;
            data.table[res_index].not_active = true;
            data_table.push(data.table[res_index])

            console.log('data talbe', data_table);
            socket.emit('s7Error', {Error: 'NoConnect'})
          }
          else if ( data.table[res_index].type == 's7'){
            data.table[res_index].active = true;
            data_table.push(data.table[res_index])
          }
          res_index++;
          console.log(menge, res_index);
          if(menge <= res_index){
            console.log('save', data_table);
            VORGEGEBENE_JSON.data = data_table;
            let data = JSON.stringify(VORGEGEBENE_JSON);
            fs.writeFileSync(CONFIG_PATH, data);
          }
        });
      }
    }
    python.end();
    if (menge == 0) {
      console.log('save with out test');
      VORGEGEBENE_JSON.data = data_table;
      let data = JSON.stringify(VORGEGEBENE_JSON);
      fs.writeFileSync(CONFIG_PATH, data);
    }
    */
  });
  socket.on('get_Table', ()=>{
    fs.readFile(CONFIG_PATH, (err, data) => {
      if(err)
        return

      let config = JSON.parse(data);
      console.log(config);
      socket.emit('get_Table_back',{table: config.data });
    });
  })
});

http.listen(8000, ()=>{
  console.log('listening on *:8000');
});
