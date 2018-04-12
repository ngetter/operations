import { Injectable, Pipe } from '@angular/core';

/*
  Generated class for the Exists pipe.

  See https://angular.io/docs/ts/latest/guide/pipes.html for more info on
  Angular 2 Pipes.
*/
@Pipe({
  name: 'exists'
})
@Injectable()
export class Exists {
  /*
    Takes a value and makes it lowercase.
   */
  transform(value: any, args: any[]) {
    if (value == 'אחר')
      return 'paper-plane';
    else if (value == 'חניך')
      return 'rose';
    else return 'school'
  }
}
