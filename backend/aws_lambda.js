'use strict';
var aws = require('aws-sdk');
var ses = new aws.SES({
    region: 'us-east-1'
});

var receivers = ['contact@primordialanalytics.com'];
var sender = 'contact@primordialanalytics.com';

exports.handler = function(event, context, callback) {

    console.log('Incoming event:', event);
    var data = JSON.parse(event.body);
    console.log(data);

    var params = {
        Destination: {
            ToAddresses: receivers
        },
        Message: {
            Body: {
                Text: {
                    Data: 'Name: ' + data.name +
                        '\nEmail: ' + data.email +
                        '\nPhone: ' + data.phone +
                        '\nMessage: ' + data.message,
                    Charset: 'UTF-8'
                }
            },
            Subject: {
                Data: 'Contact Form inquiry: ' + data.name,
            }
        },
        Source: sender
    };

    var response = {
        "statusCode": null,
        "isBase64Encoded": false,
        "headers": {
            "Access-Control-Allow-Origin": "*"
        },
        "body": JSON.stringify({
            "status": null,
            "err": null
        })
    };

    console.log('===SENDING EMAIL===');

    console.log(params);

    ses.sendEmail(params, function(err, data) {
        if (err) {
            console.log("===EMAIL FAILED===");
            response.statusCode = 500;
            response.body = JSON.stringify({
                "status": "Failure",
                "err": err
            });
            callback(null, response);
        }
        else {
            console.log("===EMAIL SENT===");
            response.statusCode = 200;
            response.body = JSON.stringify({
                "status": "Success"
            });
            callback(null, response);
            context.succeed(event);
        }
    });
};
