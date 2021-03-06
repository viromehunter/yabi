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

/**
 * YabiAcceptedExtensionList
 * create a new accepted extension list, which will allow simpler filtering
 * of inputs and validation
 */
function YabiAcceptedExtensionList(obj) {
  this.payload = obj;
  this.allowsBatching = false;

  this.containerEl = document.createElement('div');
  this.containerEl.setAttribute('class', 'acceptedExtensionList');

  var acceptedExtensionEl;
  this.acceptedExtensions = [];
  this.acceptedExtensionEls = [];

  if (!Y.Lang.isUndefined(obj)) {
    if (Y.Lang.isArray(obj)) {
      // this.containerEl.appendChild(document.createTextNode(" accepts "));

      for (index in this.payload) {
        acceptedExtensionEl = document.createElement('span');
        acceptedExtensionEl.setAttribute('class', 'acceptedExtension');
        acceptedExtensionEl.appendChild(document.createTextNode(obj[index]));
        this.containerEl.appendChild(acceptedExtensionEl);

        //space to allow line wrap
        this.containerEl.appendChild(document.createTextNode(' '));

        this.acceptedExtensionEls.push(acceptedExtensionEl);
        this.acceptedExtensions.push(obj[index]);
      }
    } else {
      // this.containerEl.appendChild(document.createTextNode(" accepts "));

      acceptedExtensionEl = document.createElement('span');
      acceptedExtensionEl.setAttribute('class', 'acceptedExtension');
      acceptedExtensionEl.appendChild(document.createTextNode(obj));
      this.containerEl.appendChild(acceptedExtensionEl);

      this.acceptedExtensionEls.push(acceptedExtensionEl);
      this.acceptedExtensions.push(obj.acceptedExtension);
    }
  }
}


/**
 * validForValue
 *
 * returns true or false on whether the value specified matches
 * all validation requirements
 */
YabiAcceptedExtensionList.prototype.validForValue = function(value) {

  //if value is empty, fall through
  if (value === null || value === '') {
    return true;
  }

  var extensions, finalExtension, arr;

  //if we have no accepted extensions, then we allow everything
  if (this.acceptedExtensions === null ||
      !Y.Lang.isArray(this.acceptedExtensions) ||
      this.acceptedExtensions.length === 0) {
    return true;
  }

  // cast YabiJobFileValues as strings, to allow the same code
  // to be used further down
  if (Y.Lang.isObject(value) && value instanceof YabiJobFileValue) {
    value = value.filename;
  }

  //if it is a job, then examine its output filetypes and allow if any pass
  if (Y.Lang.isObject(value) && value instanceof YabiJob) {
    //console.log(value + " is object");

    // Allow a job which presently emits no files to pass validation.
    if (value.emittedFiles().length == 1) {
      return true;
    }

    extensions = value.outputExtensions;
    if (!Y.Lang.isArray(extensions)) {
      extensions = [extensions];
    }

    for (var index in extensions) {
      // if the job emitting does not accept inputs and emits an extension of *
      // then do not allow the job to emit * if it has no other emitted files i
      // that are valid (this prevents file selectors from emitting
      // invalid values)

      if (!value.acceptsInput && extensions[index] == '*') {
        //if any params emit valid values for this param, then validate
        for (var bindex in value.params) {
          if (!value.params[bindex].valid) {
            continue;
          }

          if (Y.Lang.isArray(value.params[bindex].emittedFiles())) {
            for (var subindex in value.params[bindex].emittedFiles()) {
              arr = value.params[bindex].emittedFiles();
              if (this.validForValue(arr[subindex])) {
                return true;
              }
            }
          } else {
            if (this.validForValue(value.params[bindex].emittedFiles())) {
              return true;
            }
          }

        }

        //otherwise, invalid
        return false;
      }

      if (this.validForExtension(extensions[index])) {
        return true;
      }
    }

    //if we fall through to here, return false
    return false;
  } else {
    if (Y.Lang.isUndefined(value) || value === null) {
      return false;
    }

    return this.validForExtension(value);
  }

  return false;
};

// TODO we glob check not check for extensions anymore - rename stuff later
YabiAcceptedExtensionList.prototype.validForExtension = function(value) {
  //if this is a batch param, then always accept zip
  var i, glob;
  if (this.allowsBatching &&
      (value == '*' || Yabi.util.doesGlobMatch(value, '*.zip'))) {
    return true;
  }
  for (i = 0; i < this.acceptedExtensions.length; i++) {
    glob = this.acceptedExtensions[i];
    if (glob === '*' || Yabi.util.doesGlobMatch(value, glob)) {
      return true;
    }
  }

  return false;
};

