import { Component } from '@angular/core';
import { NavController } from 'ionic-angular';
import { Http } from '@angular/http';
import 'rxjs/add/operator/map'
@Component({
  templateUrl: 'build/pages/home/home.html'
})
export class HomePage {
  operations: any;
  constructor(public navCtrl: NavController, public http: Http) {

        this.http.get('https://opsign.herokuapp.com/api/list').map(res => res.json()).subscribe(data =>{
          this.operations = data.data;
          console.log (this.operations);
        });
      console.log('WOHA STARTING');
       this.operations = [
            {'date':'06.3','instructor':'זוהר דה ולאנסה','color':'secondary'},
            {'date':'07.3','instructor':'יצחק חלפי','color':'secondary'},
            {'date':'23.3','instructor':'יצחק חלפי','color':'secondary'},
            {'date':'24.3','instructor':'שחר גולדברג','color':'secondary'}
        ];
 
    }
  
  me2(item){
    item.color = 'danger';
  }
}
