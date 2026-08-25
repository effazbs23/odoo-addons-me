odoo.define('natural_foods.deal_countdown', function (require) {
"use strict";

var publicWidget = require('web.public.widget');

publicWidget.registry.DealCountdown = publicWidget.Widget.extend({
selector: '#deal-countdown',

start: function () {

    var endTime = this.el.dataset.end;
    if (!endTime) return;

    var end = new Date(endTime).getTime();

    setInterval(function () {

        var now = new Date().getTime();
        var diff = end - now;

        if (diff <= 0) return;

        var days = Math.floor(diff / (1000 * 60 * 60 * 24));
        var hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
        var minutes = Math.floor((diff / 1000 / 60) % 60);
        var seconds = Math.floor((diff / 1000) % 60);

        document.getElementById("deal-days").innerText = days;
        document.getElementById("deal-hours").innerText = hours;
        document.getElementById("deal-minutes").innerText = minutes;
        document.getElementById("deal-seconds").innerText = seconds;

    }, 1000);
},
});

});