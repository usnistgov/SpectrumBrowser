/*
* Conditions Of Use 
* 
* This software was developed by employees of the National Institute of
* Standards and Technology (NIST), and others. 
* This software has been contributed to the public domain. 
* Pursuant to title 15 Untied States Code Section 105, works of NIST
* employees are not subject to copyright protection in the United States
* and are considered to be in the public domain. 
* As a result, a formal license is not needed to use this software.
* 
* This software is provided "AS IS."  
* NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
* OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
* AND DATA ACCURACY.  NIST does not warrant or make any representations
* regarding the use of the software or the results thereof, including but
* not limited to the correctness, accuracy, reliability or usefulness of
* this software.
*/
package gov.nist.spectrumbrowser.client;

import java.util.Set;

import com.google.gwt.json.client.JSONNumber;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.ui.Composite;
import com.google.gwt.user.client.ui.Tree;
import com.google.gwt.user.client.ui.TreeItem;

public class JSONViewer extends Composite {

	public JSONViewer(JSONObject jsonObject, String rootName) {
		Tree tree = new Tree();
		initWidget(tree);
		TreeItem rootItem = tree.addTextItem(rootName);
		populate(rootItem,jsonObject);
	}

	private void populate(TreeItem root, JSONObject jsonObject) {
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

	}

}
