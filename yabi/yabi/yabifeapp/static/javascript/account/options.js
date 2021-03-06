/*
 * Yabi - a sophisticated online research environment for Grid, High Performance
 * and Cloud computing.
 * Copyright (C) 2015  Centre for Comparative Genomics, Murdoch University.
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU Affero General Public License as
 *  published by the Free Software Foundation, either version 3 of the
 *  License, or (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU Affero General Public License for more details.
 *
 *  You should have received a copy of the GNU Affero General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *  */

var YabiAccountOptions = function(account) {
  var self = this;

  this.account = account;
  this.item = this.account.list.createItem('user options');
  this.list = null;

  this.item.addEventListener('deselect', function() {
    self.account.destroyRightColumn();
    self.destroyList();
  });

  this.item.addEventListener('select', function() {
    self.createList();
  });
};

YabiAccountOptions.prototype.createList = function() {
  this.destroyList();

  this.list = new RadioList(document.querySelector('.yabiMiddleColumn'));
  this.password = new YabiAccountPassword(this);

  this.list.selectItem(this.list.items[0]);
};

YabiAccountOptions.prototype.destroyList = function() {
  if (this.list) {
    this.list.destroy();
    this.list = null;
  }
};


var YabiAccountPassword = function(options) {
  var self = this;

  this.options = options;
  this.container = null;
  this.item = this.options.list.createItem('change password');
  this.template = document.getElementById('optionsPassword');

  this.item.addEventListener('deselect', function() {
    if (self.container) {
      document.querySelector('.yabiRightColumn').removeChild(self.container);
      self.container = null;
      self.form = null;
    }
  });

  this.item.addEventListener('select', function() {
    if (self.container) {
      document.querySelector('.yabiRightColumn').removeChild(self.container);
    }

    self.container = self.template.cloneNode(true);
    self.container.className = null;
    self.container.id = null;
    self.form = self.container.querySelector('form');

    document.querySelector('.yabiRightColumn').appendChild(self.container);

    Y.use('*', function(Y) {
      var containerNode = Y.one(self.container);

      Y.on('submit', function(e) {
        e.preventDefault();

        var currentPassword = self.container.querySelector(
            "input[name='currentPassword']").value;
        var newPassword = self.container.querySelector(
            "input[name='newPassword']").value;
        var confirmPassword = self.container.querySelector(
            "input[name='confirmPassword']").value;

        if (newPassword == confirmPassword) {
          if (newPassword.length >= 6) {
            var callback = {
              success: function(trans_id, o) {
                YAHOO.ccgyabi.widget.YabiMessage.handleResponse(o);

                self.enableForm();
                self.form.reset();
              },
              failure: function(trans_id, o) {
                YAHOO.ccgyabi.widget.YabiMessage.handleResponse(o);
                self.enableForm();
              }
            };

            var cfg = {
              method: 'POST',
              form: { id: self.container.querySelector('form') },
              on: callback
            };

            Yabi.util.setCSRFHeader(Y.io);
            var request = Y.io(appURL + 'account/password', cfg);

            self.disableForm();
          } else {
            YAHOO.ccgyabi.widget.YabiMessage.fail(
                'The new password must be at least 6 characters in length');
          }
        } else {
          YAHOO.ccgyabi.widget.YabiMessage.fail('The new passwords must match');
        }
      });
    });
  });
};

YabiAccountPassword.prototype.disableForm = function() {
  var elements = this.form.querySelectorAll('input, select, textarea');

  for (var i = 0; i < elements.length; i++) {
    elements[i].enabled = false;
  }
};

YabiAccountPassword.prototype.enableForm = function() {
  var elements = this.form.querySelectorAll('input, select, textarea');

  for (var i = 0; i < elements.length; i++) {
    elements[i].enabled = true;
  }
};
