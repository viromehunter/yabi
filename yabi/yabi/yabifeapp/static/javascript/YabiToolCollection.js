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

ToolCollectionYUI = YUI().use(
    'node', 'event', 'dd-drag', 'dd-proxy', 'dd-drop', 'io', 'json-parse',
    function(Y) {

      /**
       * YabiToolCollection
       * fetch and render listing/grouping/smart filtering of tools
       */
      YabiToolCollection = function() {
        this.tools = [];
        this.toolMap = {};

        this.autofilter = true;

        this.containerNode = Y.Node.create('<div class="toolCollection"/>');
        var filterEl = Y.Node.create('<div class="filterPanel"/>');

        this.searchLabelEl = Y.Node.create("<label>Find tool: </label>");
        filterEl.append(this.searchLabelEl);

        this.searchNode = Y.Node.create('<input type="search" class="toolSearchField">');

        //attach key events for changes/keypresses
        this.searchNode.on('blur', this.filterCallback, null, this);
        this.searchNode.on('keyup', this.filterCallback, null, this);
        this.searchNode.on('change', this.filterCallback, null, this);
        this.searchNode.on('search', this.filterCallback, null, this);

        filterEl.append(this.searchNode);

        this.clearFilterNode = Y.Node.create('<span class="fakeButton">show all</span>');
        this.clearFilterNode.hide();
        this.clearFilterNode.on('click', this.clearFilterCallback, null, this);

        filterEl.append(this.clearFilterNode);

        //autofilter
        this.autofilterContainer = document.createElement('div');
        this.autofilterContainer.className = 'autofilterContainer';
        this.autofilterContainer.appendChild(document.createTextNode(
            'Use selection to auto-filter?'));

        this.autofilterEl = document.createElement('span');
        this.autofilterEl.className = 'virtualCheckboxOn';
        this.autofilterEl.appendChild(document.createTextNode('on'));

        Y.one(this.autofilterEl).on('click', this.autofilterCallback, this);
        this.autofilterContainer.appendChild(this.autofilterEl);

        filterEl.append(this.autofilterContainer);

        this.containerNode.append(filterEl);

        //no results div
        this.noResultsDiv = Y.Node.create('<div class="wfNoResultsDiv">no matching tools</div>');
        this.containerNode.append(this.noResultsDiv);

        this.listingNode = Y.Node.create('<div class="toolListing"/>');

        this.loading = new YAHOO.ccgyabi.widget.Loading(this.listingNode.getDOMNode());
        this.loading.show();

        this.containerNode.append(this.listingNode);

        this.searchNode.set("value", "select");
        this.filter();

        this.hydrate();
      };

      YabiToolCollection.registerDDTarget = function(node) {
        new Y.DD.Drop({ node: node });
      };

      YabiToolCollection.prototype.solidify = function(obj) {
        this.payload = obj;

        this.loading.hide();

        var fixupTool = function(tooldef) {
          // convert jobs in saved workflows to tools
          this.toolMap[tooldef.name] = tooldef;
          if (tooldef.json) {
            _.forEach(tooldef.json.jobs, function(job) {
              _.assign(job, this.toolMap[job.toolName]);
            }, this);
          }

          return tooldef;
        };

        _.forEach(obj.menu.toolsets, function(toolset) {
          _.forEach(toolset.toolgroups, function(toolgroup) {
            var groupNode = Y.Node.create('<div class="toolGroup"/>');
            groupNode
              .set("text", toolgroup.name)
              .addClass(toolset.name);
            this.listingNode.append(groupNode);

            _(toolgroup.tools).map(fixupTool, this).forEach(function(tooldef) {
              var tool = new YabiTool(tooldef, this, groupNode);

              tool.node.appendTo(this.listingNode).addClass(toolset.name);

              //drag drop
              var dd = new Y.DD.Drag({
                node: tool.node,
                data: {
                  tool: tool
                }
                //startCentered: true,
              }).plug(Y.Plugin.DDProxy, {
                moveOnEnd: false
              });

              dd.on('drag:start', this.startDragToolCallback, this);
              dd.on('drag:end', workflow.endDragJobCallback);
              dd.on('drag:drag', workflow.onDragJobCallback);
              dd.on('drag:over', workflow.onDragOverJobCallback);

              this.tools.push(tool);
            }, this);

          }, this);
        }, this);

        this.filter();
      };


      /**
       * hydrate
       *
       * performs an AJAX json fetch of all the tool details and data
       *
       */
      YabiToolCollection.prototype.hydrate = function() {
        Y.io(appURL + 'ws/menu/', {
          on: {
            complete: function(transId, o) {
              this.hydrateResponse(o);
              this.hydrateSavedWorkflows();
            }
          },
          context: this
        });
      };

      /**
       * hydrateSavedWorkflows
       *
       * performs another AJAX json fetch to get saved workflows
       *
       */
      YabiToolCollection.prototype.hydrateSavedWorkflows = function() {
        Y.io(appURL + 'ws/menu_saved_workflows/', {
          on: {
            complete: function(transId, o) {
              this.hydrateResponse(o);
            }
          },
          context: this
        });
      };

      YabiToolCollection.prototype.toString = function() {
        return 'tool collection';
      };


      /**
       * filter
       *
       * use the search field to limit visible tools
       */
      YabiToolCollection.prototype.filter = function() {
        var filterVal = this.searchNode.get("value");
        var visibleCount = 0;

        this.clearFilterNode.toggleView(filterVal !== '');

        Y.all(".toolGroup").hide();

        _.forEach(this.tools, function(tool) {
          if (tool.matchesFilter(filterVal)) {
            tool.node.show();
            tool.groupNode.show();
            visibleCount++;
          } else {
            tool.node.hide();
          }
        });

        this.noResultsDiv.toggleView(visibleCount === 0 && this.tools.length !== 0);
      };


      /**
       * clearFilter
       */
      YabiToolCollection.prototype.clearFilter = function() {
        this.searchNode.set("value", "");
        this.filter();
      };


      /**
       * autofilterToggle
       */
      YabiToolCollection.prototype.autofilterToggle = function() {
        this.autofilter = !this.autofilter;

        if (this.autofilter) {
          this.autofilterEl.className = 'virtualCheckboxOn';
          this.autofilterEl.innerHTML = 'on';
        } else {
          this.autofilterEl.className = 'virtualCheckbox';
          this.autofilterEl.innerHTML = 'off';
        }
      };

      // ----- callback methods, these require a target via their inputs -----


      /**
       * filterCallback
       *
       */
      YabiToolCollection.prototype.filterCallback = function(e, target) {
        target.filter();
      };


      /**
       * clearFilterCallback
       *
       */
      YabiToolCollection.prototype.clearFilterCallback = function(e, target) {
        target.clearFilter();
      };


      /**
       * autofilterCallback
       *
       * toggle autofiltering
       */
      YabiToolCollection.prototype.autofilterCallback = function(e) {
        this.autofilterToggle();
      };


      /**
       * addToolToWorkflow
       *
       * adds a YabiTool to the workflow.
       * returns the list of jobs added.
       */
      YabiToolCollection.prototype.addToolToWorkflow = function(tool, provisional) {
        var addJob = function(name, id, preload) {
          var job = workflow.addJob(name, id, preload, false);
          if (provisional) {
            job.container.setStyle("opacity", '0.1');
            job.optionsNode.hide();
          }
          return job;
        };

        var jobs;

        if (!tool.isSavedWorkflow()) {
          jobs = [addJob(tool.toString(), tool.payload.toolId)];
        } else {
          if (workflow.isEmpty() && workflow.nameIsUnchanged()) {
            workflow.setInitialName(tool.getTitle());
          }

          jobs = _.map(tool.getWorkflowJobs(), function(job) {
            return addJob(job.toolName, job.toolId, job.parameterList.parameter);
          });
          workflow.workflowLoaded = false;
          workflow.setupJobsList = jobs;
        }

        return jobs;
      };


      /**
       * hydrateResponse
       *
       * handle the response
       * parse json, store internally
       */
      YabiToolCollection.prototype.hydrateResponse = function(o) {
        var obj;

        try {
          obj = Y.JSON.parse(o.responseText);
        } catch (e) {
          YAHOO.ccgyabi.widget.YabiMessage.handleResponse(o);
          obj = {'menu': {'toolsets': []}};
        }

        this.solidify(obj);
      };

      YabiToolCollection.prototype.startDragToolCallback = function(e) {
        // work out which tool it is
        var tool = e.target.get('data').tool;

        if (Y.Lang.isUndefined(tool)) {
          YAHOO.ccgyabi.widget.YabiMessage.fail('Failed to find tool');
          return false;
        }

        var jobs = this.addToolToWorkflow(tool, true);

        e.target.jobNodes = new Y.NodeList(_.pluck(jobs, "container"));
        e.target.optionsNode = jobs[jobs.length - 1].optionsNode;

        var dragNode = e.target.get('dragNode');
        dragNode.set('innerHTML', e.target.get('node').get('innerHTML'));
        dragNode.setStyles({
          border: 'none',
          textAlign: 'left'
        });
        // remove the 'add' image from the dragged item
        dragNode.one(".addLink").remove();

        e.target.dragType = 'tool';
        e.target.lastY = dragNode.getY();
      };


    }); // end of YUI().use(
