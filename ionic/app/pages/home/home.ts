import { Component } from '@angular/core';
import { NavController, ModalController } from 'ionic-angular';
import { Http, Headers, RequestOptions } from '@angular/http';
import 'rxjs/add/operator/map'
import { D2S } from '../../pipes/d2s';
import { ParticipantsPage } from '../participants/participants';
import { SigninPage } from '../signin/signin';

@Component({
  templateUrl: 'build/pages/home/home.html',
  pipes: [D2S]
})
export class HomePage {
  operations: any;

  constructor(public navCtrl: NavController, public http: Http, private modalCtrl: ModalController) {

        this.http.get('https://opsign.herokuapp.com/api/list').map(res => res.json()).subscribe(data =>{
          this.operations = data.data;
        });
        
        //TODO: search on each operation.participants for user email. if exsists mark mein = true

    }
  
  participants(item){
  
    var headers = new Headers();
    headers.append("Accept", 'application/json');
    headers.append('Content-Type', 'application/json' );
    let options = new RequestOptions({ headers: headers });
    let body = JSON.stringify({id: item._id.$oid});
    console.log(body);
    this.http.post('https://opsign.herokuapp.com/api/getparticipants',body,options)
    .map(res => res.json()).subscribe(data =>{
          console.log(data);
          this.navCtrl.push(ParticipantsPage, {participants: data.data});
    });
    
  }
  
  me2(item){
    //TODO: send get request to include user in participants
    let user = localStorage.getItem('user');
    if (user==null){
      let myModal = this.modalCtrl.create(SigninPage);
      myModal.onDidDismiss(data => {
        console.log(data);
      });
      myModal.present();
    }
    
    var headers = new Headers();
    headers.append("Accept", 'application/json');
    headers.append('Content-Type', 'application/json' );
    let options = new RequestOptions({ headers: headers });
    let body = JSON.stringify({id: item._id.$oid, username: user});

    this.http.post('https://opsign.herokuapp.com/mark_arrival',  body, options)
    .map(data => data.json()).subscribe(result => {
      console.log(result);
      if (result.participate)
        item.bcolor='secondary';
      else
        item.bcolor = 'primary';
      item.cadets = result.length;
    });



  }
    
    
}

