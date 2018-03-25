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
    let participants = item.participate;
    this.navCtrl.push(ParticipantsPage, {participants: participants});
  }
  
  me2(item){
    if (('bcolor' in item) && item.bcolor == 'secondary'){
      item.bcolor='primary';
      //TODO: send get request to exclude user from participants
      item.pilots -= 1;
    }
    else{
      item.bcolor='secondary';
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
      .subscribe((result)=> {console.log(result)});


      if ('pilots' in item)
        item.pilots += 1;
      else
        item.pilots = 1;
    }
    
    
  }
}
