import { Component } from '@angular/core';
import { NavController } from 'ionic-angular';
import { Http } from '@angular/http';
import 'rxjs/add/operator/map'
import { D2S } from '../../pipes/d2s';

@Component({
  templateUrl: 'build/pages/home/home.html',
  pipes: [D2S]
})
export class HomePage {
  operations: any;

  constructor(public navCtrl: NavController, public http: Http) {

        this.http.get('https://opsign.herokuapp.com/api/list').map(res => res.json()).subscribe(data =>{
          this.operations = data.data;
        });
        
        //TODO: search on each operation.participants for user email. if exsists mark mein = true

        localStorage.setItem('user', 'ngetter@gmail.com');
    }
  
  me2(item){
      let user = localStorage.getItem('user');
      let body = {id: item._id, username:user};
      console.log(body);
      
      this.http.post('https://opsign.herokuapp.com/mark_arrival',  JSON.stringify(body));
    if (('bgcolor' in item) && item.bcolor == 'secondary'){
      item.bcolor='primary';
      //TODO: send get request to exclude user from participants
      item.pilots -= 1;
    }
    else{
      item.bcolor='secondary';
      //TODO: send get request to include user in participants


      if ('pilots' in item)
        item.pilots += 1;
      else
        item.pilots = 1;
    }
    
    
  }
}
