package gov.nist.spectrumbrowser.admin;

import java.util.Set;

import com.google.gwt.json.client.JSONNumber;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.Tree;
import com.google.gwt.user.client.ui.TreeItem;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;


public class JSONViewer extends Composite {
	Admin admin;
	ShowMessageDates showMessageDates;
	VerticalPanel verticalPanel;
	Sensor sensor;
	JSONObject jsonObject;
	String rootName;
	public JSONViewer(JSONObject jsonObject, String rootName, Admin admin, ShowMessageDates showMessageDates, VerticalPanel verticalPanel, Sensor sensor) {
		this.verticalPanel = verticalPanel;
		this.showMessageDates = showMessageDates;
		this.sensor = sensor;
		this.admin = admin;
		this.jsonObject = jsonObject;
		this.rootName = rootName;
 	}
	
	public void draw() {

		Tree tree = new Tree();
		HorizontalPanel hpanel = new HorizontalPanel();
		JSONObject strJ = (JSONObject) jsonObject.get(rootName);
		TreeItem rootItem = tree.addTextItem(rootName);
		TreeItem madAdder = populate(rootItem,strJ);
		Button okButton = new Button("OK");
		Button logoffButton = new Button("Log Off");

		verticalPanel.clear();
		madAdder.setState(true);
		tree.addItem(madAdder);
	
		
		okButton.addClickHandler(new ClickHandler(){

			@Override
			public void onClick(ClickEvent event) {
				showMessageDates.draw();
				
			}});
		hpanel.add(okButton);
		
		logoffButton.addClickHandler (new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				admin.logoff();
			}});
		
		hpanel.add(logoffButton);
				
                verticalPanel.add(tree);
		verticalPanel.add(hpanel);
		initWidget(verticalPanel);
	
	}

	private TreeItem populate(TreeItem root, JSONObject jsonObject) {
		Set<String> keySet = jsonObject.keySet();
		for (String key : keySet) {
			JSONValue jsonValue = jsonObject.get(key);
			JSONString jsonString = jsonValue.isString();
			JSONNumber jsonNumber = jsonValue.isNumber();
			TreeItem treeItem =  root.addTextItem(key);
			if (jsonString != null) {
				String stringValue = jsonString.stringValue();
				treeItem.addTextItem(stringValue);
			} else if (jsonNumber != null ) {
				String stringValue = Double.toString(jsonNumber.doubleValue());
				treeItem.addTextItem(stringValue);
			} else if (jsonValue.isObject() != null) {
				populate(treeItem,jsonValue.isObject());
			}
		}
		
		return root;

	}

}
