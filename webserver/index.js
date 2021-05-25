const express = require('express');
const app = express();
const http = require('http').Server(app);
const io = require('socket.io')(http);
const fs = require('fs');
const axios = require('axios');
const bcrypt = require('bcryptjs');

let pythonBridge = require('python-bridge');
const USERS_PATH = __dirname +  '/users.json';
const CONFIG_PATH = __dirname + '/../config.json'


const VORGEGEBENE_JSON = {
  "domain":"https://cloud.enwatmon.de",
  "data": []
}

app.use(express.static(__dirname + '/client/'));
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
  socket.on('set_Table', ({table})=>{
    console.log('save with out test');

    fs.readFile(CONFIG_PATH, (err, data) => {
      if (err){
        console.log(err);
        VORGEGEBENE_JSON.data = table
        for (var line of VORGEGEBENE_JSON.data) {
          if (line.type == 'static' && (line.type == 'MAD' || line.type == 'mad')) {
            VORGEGEBENE_JSON.mad = line.value;
          }
        }
        let data_to_write = JSON.stringify(VORGEGEBENE_JSON);
        fs.writeFileSync(CONFIG_PATH, data_to_write);
        return
      }

      let config = JSON.parse(data);
      config.data = table;
      for (var line of config.data) {
        if (line.type == 'static' && (line.type == 'MAD' || line.type == 'mad')) {
          config.mad = line.value;
        }
      }

      let data_to_write = JSON.stringify(config);
      fs.writeFileSync(CONFIG_PATH, data_to_write);

    });

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
