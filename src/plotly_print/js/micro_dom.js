/**
 * plotly-print Micro-DOM for Plotly.js / D3 v3 static rendering in QuickJS.
 */
(function() {
    'use strict';

    var globalScope = typeof globalThis !== 'undefined' ? globalThis : this;
    if (typeof globalScope.process === 'undefined') {
        globalScope.process = { env: { NODE_ENV: 'production' }, browser: true, version: '' };
    }

    // --- Helpers ---
    function camelToDashed(str) {
        return str.replace(/[A-Z]/g, function(m) { return '-' + m.toLowerCase(); });
    }

    // --- CSSStyleDeclaration ---
    function CSSStyleDeclaration() {
        this._properties = {};
    }
    CSSStyleDeclaration.prototype.setProperty = function(name, value, priority) {
        if (value === null || value === undefined || value === '') {
            delete this._properties[name];
        } else {
            this._properties[name] = String(value);
        }
    };
    CSSStyleDeclaration.prototype.getPropertyValue = function(name) {
        return this._properties[name] || '';
    };
    CSSStyleDeclaration.prototype.removeProperty = function(name) {
        var val = this._properties[name] || '';
        delete this._properties[name];
        return val;
    };
    CSSStyleDeclaration.prototype.cssText = function() {
        var parts = [];
        for (var k in this._properties) {
            parts.push(camelToDashed(k) + ': ' + this._properties[k]);
        }
        return parts.join('; ');
    };

    // Style proxy or property reflection
    function createStyle() {
        var decl = new CSSStyleDeclaration();
        // Return a proxy if available, else plain decl with getters/setters for common props
        if (typeof Proxy !== 'undefined') {
            return new Proxy(decl, {
                get: function(target, prop) {
                    if (prop in target || typeof prop === 'symbol') {
                        return target[prop];
                    }
                    var dashed = camelToDashed(String(prop));
                    return target.getPropertyValue(dashed);
                },
                set: function(target, prop, value) {
                    if (prop === '_properties' || prop in target) {
                        target[prop] = value;
                    } else {
                        var dashed = camelToDashed(String(prop));
                        target.setProperty(dashed, value);
                    }
                    return true;
                }
            });
        }
        return decl;
    }

    // --- DOM Node ---
    function Node() {
        this.childNodes = [];
        this.parentNode = null;
        this._ownerDoc = null;
        this.nodeType = 1;
        this.nodeName = '';
    }

    Object.defineProperty(Node.prototype, 'ownerDocument', {
        get: function() {
            if (this.nodeType === 9) return null;
            return this._ownerDoc || (globalScope.document || null);
        },
        set: function(v) {
            this._ownerDoc = v;
        }
    });

    Object.defineProperty(Node.prototype, 'firstChild', {
        get: function() { return this.childNodes[0] || null; }
    });
    Object.defineProperty(Node.prototype, 'lastChild', {
        get: function() { return this.childNodes[this.childNodes.length - 1] || null; }
    });
    Object.defineProperty(Node.prototype, 'nextSibling', {
        get: function() {
            if (!this.parentNode) return null;
            var idx = this.parentNode.childNodes.indexOf(this);
            return (idx !== -1 && idx + 1 < this.parentNode.childNodes.length) ? this.parentNode.childNodes[idx + 1] : null;
        }
    });
    Object.defineProperty(Node.prototype, 'previousSibling', {
        get: function() {
            if (!this.parentNode) return null;
            var idx = this.parentNode.childNodes.indexOf(this);
            return (idx > 0) ? this.parentNode.childNodes[idx - 1] : null;
        }
    });

    Node.prototype.appendChild = function(child) {
        if (child.nodeType === 11) { // DocumentFragment
            var children = child.childNodes.slice();
            for (var i = 0; i < children.length; i++) {
                this.appendChild(children[i]);
            }
            return child;
        }
        if (child.parentNode) {
            child.parentNode.removeChild(child);
        }
        child.parentNode = this;
        child._ownerDoc = this.nodeType === 9 ? this : (this.ownerDocument || globalScope.document);
        this.childNodes.push(child);
        return child;
    };

    Node.prototype.removeChild = function(child) {
        var idx = this.childNodes.indexOf(child);
        if (idx !== -1) {
            this.childNodes.splice(idx, 1);
            child.parentNode = null;
            return child;
        }
        return child;
    };

    Node.prototype.insertBefore = function(newChild, refChild) {
        if (!refChild) return this.appendChild(newChild);
        if (newChild.nodeType === 11) { // DocumentFragment
            var children = newChild.childNodes.slice();
            for (var i = 0; i < children.length; i++) {
                this.insertBefore(children[i], refChild);
            }
            return newChild;
        }
        if (newChild.parentNode) {
            newChild.parentNode.removeChild(newChild);
        }
        var idx = this.childNodes.indexOf(refChild);
        if (idx !== -1) {
            newChild.parentNode = this;
            newChild.ownerDocument = this.ownerDocument || this;
            this.childNodes.splice(idx, 0, newChild);
            return newChild;
        }
        return this.appendChild(newChild);
    };

    Node.prototype.replaceChild = function(newChild, oldChild) {
        this.insertBefore(newChild, oldChild);
        return this.removeChild(oldChild);
    };

    Node.prototype.cloneNode = function(deep) {
        var clone;
        if (this.nodeType === 3) {
            clone = new Text(this.nodeValue);
        } else if (this.nodeType === 1) {
            clone = this.namespaceURI 
                ? (this.ownerDocument || document).createElementNS(this.namespaceURI, this.tagName.toLowerCase())
                : (this.ownerDocument || document).createElement(this.tagName.toLowerCase());
            for (var k in this._attributes) {
                clone.setAttribute(k, this._attributes[k]);
            }
            for (var prop in this.style._properties) {
                clone.style.setProperty(prop, this.style.getPropertyValue(prop));
            }
        } else {
            clone = new Node();
        }
        if (deep && this.childNodes) {
            for (var i = 0; i < this.childNodes.length; i++) {
                clone.appendChild(this.childNodes[i].cloneNode(true));
            }
        }
        return clone;
    };

    Object.defineProperty(Node.prototype, 'textContent', {
        get: function() {
            if (this.nodeType === 3) return this.nodeValue;
            var txt = '';
            for (var i = 0; i < this.childNodes.length; i++) {
                txt += this.childNodes[i].textContent || '';
            }
            return txt;
        },
        set: function(val) {
            this.childNodes = [];
            if (val !== null && val !== undefined && val !== '') {
                this.appendChild(new Text(String(val)));
            }
        }
    });

    // --- Text Node ---
    function Text(text) {
        Node.call(this);
        this.nodeType = 3;
        this.nodeName = '#text';
        this.nodeValue = String(text !== undefined && text !== null ? text : '');
    }
    Text.prototype = Object.create(Node.prototype);
    Object.defineProperty(Text.prototype, 'data', {
        get: function() { return this.nodeValue; },
        set: function(v) { this.nodeValue = String(v); }
    });

    // --- DocumentFragment ---
    function DocumentFragment() {
        Node.call(this);
        this.nodeType = 11;
        this.nodeName = '#document-fragment';
    }
    DocumentFragment.prototype = Object.create(Node.prototype);

    // --- Element ---
    function Element(tagName, namespaceURI) {
        Node.call(this);
        this.nodeType = 1;
        this.namespaceURI = namespaceURI || null;
        var tagStr = String(tagName);
        if (this.namespaceURI === 'http://www.w3.org/2000/svg') {
            var lower = tagStr.toLowerCase();
            this.tagName = SVG_CAMEL_TAGS[lower] || lower;
            this.nodeName = this.tagName;
        } else {
            this.tagName = tagStr.toUpperCase();
            this.nodeName = this.tagName;
        }
        this._attributes = {};
        this.style = createStyle();
        this.classList = new ClassList(this);
        this._eventListeners = {};

        // Default dimensions
        this.clientWidth = 0;
        this.clientHeight = 0;
        this.offsetWidth = 0;
        this.offsetHeight = 0;
    }
    Element.prototype = Object.create(Node.prototype);

    Object.defineProperty(Element.prototype, 'id', {
        get: function() { return this.getAttribute('id') || ''; },
        set: function(v) { this.setAttribute('id', v); }
    });

    Object.defineProperty(Element.prototype, 'className', {
        get: function() { return this.getAttribute('class') || ''; },
        set: function(v) { this.setAttribute('class', v); }
    });

    function ClassList(el) { this._el = el; }
    ClassList.prototype.add = function() {
        var current = (this._el.getAttribute('class') || '').split(/\s+/).filter(Boolean);
        for (var i = 0; i < arguments.length; i++) {
            if (current.indexOf(arguments[i]) === -1) current.push(arguments[i]);
        }
        this._el.setAttribute('class', current.join(' '));
    };
    ClassList.prototype.remove = function() {
        var current = (this._el.getAttribute('class') || '').split(/\s+/).filter(Boolean);
        for (var i = 0; i < arguments.length; i++) {
            var idx = current.indexOf(arguments[i]);
            if (idx !== -1) current.splice(idx, 1);
        }
        this._el.setAttribute('class', current.join(' '));
    };
    ClassList.prototype.contains = function(name) {
        var current = (this._el.getAttribute('class') || '').split(/\s+/).filter(Boolean);
        return current.indexOf(name) !== -1;
    };
    ClassList.prototype.toggle = function(name) {
        if (this.contains(name)) { this.remove(name); return false; }
        else { this.add(name); return true; }
    };

    Element.prototype.setAttribute = function(name, value) {
        this._attributes[name] = String(value);
    };
    Element.prototype.getAttribute = function(name) {
        return this._attributes.hasOwnProperty(name) ? this._attributes[name] : null;
    };
    Element.prototype.hasAttribute = function(name) {
        return this._attributes.hasOwnProperty(name);
    };
    Element.prototype.removeAttribute = function(name) {
        delete this._attributes[name];
    };
    Element.prototype.setAttributeNS = function(ns, name, value) {
        this.setAttribute(name, value);
        if (name === 'href' && ns && String(ns).indexOf('xlink') !== -1) {
            this.setAttribute('xlink:href', value);
        } else if (name === 'xlink:href') {
            this.setAttribute('href', value);
        }
    };
    Element.prototype.getAttributeNS = function(ns, name) {
        return this.getAttribute(name);
    };
    Element.prototype.hasAttributeNS = function(ns, name) {
        return this.hasAttribute(name);
    };
    Element.prototype.removeAttributeNS = function(ns, name) {
        this.removeAttribute(name);
    };

    // Event listeners
    Element.prototype.addEventListener = function(event, fn) {
        if (!this._eventListeners[event]) this._eventListeners[event] = [];
        this._eventListeners[event].push(fn);
    };
    Element.prototype.removeEventListener = function(event, fn) {
        if (!this._eventListeners[event]) return;
        var idx = this._eventListeners[event].indexOf(fn);
        if (idx !== -1) this._eventListeners[event].splice(idx, 1);
    };
    Element.prototype.dispatchEvent = function(evt) {
        var fns = this._eventListeners[evt.type];
        if (fns) {
            for (var i = 0; i < fns.length; i++) {
                try { fns[i].call(this, evt); } catch(e) {}
            }
        }
        return true;
    };

    // D3 / Plotly Query Selectors
    Element.prototype.matches = function(selector) {
        if (!selector) return false;
        if (selector === '*') return true;
        if (selector === ':first-child') {
            if (!this.parentNode) return false;
            for (var i = 0; i < this.parentNode.childNodes.length; i++) {
                var ch = this.parentNode.childNodes[i];
                if (ch.nodeType === 1) return ch === this;
            }
            return false;
        }
        if (selector[0] === '#') return this.id === selector.slice(1);
        if (selector[0] === '.') {
            var cls = selector.slice(1);
            return this.classList.contains(cls);
        }

        // Attribute selector e.g. g[class^="barlayer"], [class^="barlayer"], [id="xyz"]
        var attrMatch = selector.match(/^([a-zA-Z0-9_-]*)\[([a-zA-Z0-9_-]+)([\^$*~|]?=)?(["']?)(.*?)\4\]$/);
        if (attrMatch) {
            var tag = attrMatch[1];
            var attr = attrMatch[2];
            var op = attrMatch[3];
            var val = attrMatch[5];
            if (tag && this.tagName.toLowerCase() !== tag.toLowerCase()) return false;
            if (!this.hasAttribute(attr)) return false;
            if (!op) return true;
            var actual = this.getAttribute(attr) || '';
            if (op === '=') return actual === val;
            if (op === '^=') return actual.indexOf(val) === 0;
            if (op === '$=') return actual.slice(-val.length) === val;
            if (op === '*=') return actual.indexOf(val) !== -1;
            if (op === '~=') return (' ' + actual + ' ').indexOf(' ' + val + ' ') !== -1;
            return false;
        }

        // Tag with class(es): e.g. svg.main-svg or g.trace.bars
        if (selector.indexOf('.') !== -1) {
            var parts = selector.split('.');
            var tagMatch = !parts[0] || this.tagName.toLowerCase() === parts[0].toLowerCase();
            if (!tagMatch) return false;
            for (var p = 1; p < parts.length; p++) {
                if (!this.classList.contains(parts[p])) return false;
            }
            return true;
        }
        return this.tagName.toLowerCase() === selector.toLowerCase();
    };

    Element.prototype.querySelector = function(selector) {
        if (selector === ':first-child') {
            for (var i = 0; i < this.childNodes.length; i++) {
                var ch = this.childNodes[i];
                if (ch.nodeType === 1) return ch;
            }
            return null;
        }
        var results = this.querySelectorAll(selector);
        return results.length > 0 ? results[0] : null;
    };

    function querySelectorAllSimple(root, selector) {
        var matches = [];
        function walk(node) {
            for (var i = 0; i < node.childNodes.length; i++) {
                var child = node.childNodes[i];
                if (child.nodeType === 1) {
                    if (child.matches(selector)) matches.push(child);
                    walk(child);
                }
            }
        }
        walk(root);
        return matches;
    }

    function querySelectorAllSingle(root, selector) {
        selector = selector.trim();
        if (!selector) return [];

        // Handle child combinators: e.g. "a > b > c"
        if (selector.indexOf('>') !== -1) {
            var segments = selector.split('>');
            var current = [root];
            for (var s = 0; s < segments.length; s++) {
                var seg = segments[s].trim();
                var next = [];
                for (var c = 0; c < current.length; c++) {
                    var parentNode = current[c];
                    if (s === 0) {
                        var matched = querySelectorAllSingle(parentNode, seg);
                        for (var m = 0; m < matched.length; m++) {
                            if (next.indexOf(matched[m]) === -1) next.push(matched[m]);
                        }
                    } else {
                        for (var ch = 0; ch < parentNode.childNodes.length; ch++) {
                            var kid = parentNode.childNodes[ch];
                            if (kid.nodeType === 1 && kid.matches(seg)) {
                                if (next.indexOf(kid) === -1) next.push(kid);
                            }
                        }
                    }
                }
                current = next;
            }
            return current;
        }

        // Handle space descendant combinators: e.g. "a b c"
        var inBracket = false;
        var hasSpace = false;
        for (var i = 0; i < selector.length; i++) {
            if (selector[i] === '[') inBracket = true;
            else if (selector[i] === ']') inBracket = false;
            else if (selector[i] === ' ' && !inBracket) {
                hasSpace = true;
                break;
            }
        }
        if (hasSpace) {
            var tokens = [];
            var curr = '';
            for (var i = 0; i < selector.length; i++) {
                if (selector[i] === '[') inBracket = true;
                else if (selector[i] === ']') inBracket = false;
                if (selector[i] === ' ' && !inBracket) {
                    if (curr.trim()) tokens.push(curr.trim());
                    curr = '';
                } else {
                    curr += selector[i];
                }
            }
            if (curr.trim()) tokens.push(curr.trim());

            var current = [root];
            for (var t = 0; t < tokens.length; t++) {
                var tok = tokens[t];
                var next = [];
                for (var c = 0; c < current.length; c++) {
                    var descendants = querySelectorAllSimple(current[c], tok);
                    for (var d = 0; d < descendants.length; d++) {
                        if (next.indexOf(descendants[d]) === -1) next.push(descendants[d]);
                    }
                }
                current = next;
            }
            return current;
        }

        return querySelectorAllSimple(root, selector);
    }

    Element.prototype.querySelectorAll = function(selector) {
        if (!selector) return [];
        if (selector.indexOf(',') !== -1) {
            var parts = selector.split(',');
            var all = [];
            for (var p = 0; p < parts.length; p++) {
                var res = querySelectorAllSingle(this, parts[p]);
                for (var r = 0; r < res.length; r++) {
                    if (all.indexOf(res[r]) === -1) all.push(res[r]);
                }
            }
            return all;
        }
        return querySelectorAllSingle(this, selector);
    };

    Element.prototype.getElementsByTagName = function(tagName) {
        var target = tagName.toUpperCase();
        var matches = [];
        function walk(node) {
            for (var i = 0; i < node.childNodes.length; i++) {
                var child = node.childNodes[i];
                if (child.nodeType === 1) {
                    if (target === '*' || child.tagName === target) matches.push(child);
                    walk(child);
                }
            }
        }
        walk(this);
        return matches;
    };

    Element.prototype.getElementsByClassName = function(className) {
        return this.querySelectorAll('.' + className);
    };

    // --- Geometry & Font Measurement ---
    Element.prototype.getCTM = function() {
        return identityMatrix();
    };
    Element.prototype.getScreenCTM = function() {
        return identityMatrix();
    };

    function identityMatrix() {
        return { a: 1, b: 0, c: 0, d: 1, e: 0, f: 0 };
    }

    function multiplyMatrices(m1, m2) {
        // Column-vector convention: result = m1 * m2 (m2 applied first).
        return {
            a: m1.a * m2.a + m1.c * m2.b,
            b: m1.b * m2.a + m1.d * m2.b,
            c: m1.a * m2.c + m1.c * m2.d,
            d: m1.b * m2.c + m1.d * m2.d,
            e: m1.a * m2.e + m1.c * m2.f + m1.e,
            f: m1.b * m2.e + m1.d * m2.f + m1.f
        };
    }

    function transformPoint(m, x, y) {
        return {
            x: m.a * x + m.c * y + m.e,
            y: m.b * x + m.d * y + m.f
        };
    }

    function translateMatrix(tx, ty) {
        return { a: 1, b: 0, c: 0, d: 1, e: tx || 0, f: ty || 0 };
    }

    /**
     * Parse a full SVG transform attribute into a 2D affine matrix.
     * SVG post-multiplies the list left-to-right (M = T1*T2*...*Tn), so the
     * rightmost transform is applied to a point first.
     */
    function parseTransform(transform) {
        if (!transform) return identityMatrix();
        var result = identityMatrix();
        var re = /(matrix|translate|scale|rotate|skewX|skewY)\s*\(\s*([^)]*)\s*\)/g;
        var match;
        while ((match = re.exec(String(transform))) !== null) {
            var type = match[1];
            var rawArgs = match[2].trim();
            var args = rawArgs ? rawArgs.split(/[\s,]+/).map(parseFloat) : [];
            var m = identityMatrix();

            if (type === 'matrix' && args.length >= 6) {
                m = {
                    a: args[0], b: args[1], c: args[2],
                    d: args[3], e: args[4], f: args[5]
                };
            } else if (type === 'translate') {
                m.e = args[0] || 0;
                m.f = args.length > 1 ? (args[1] || 0) : 0;
            } else if (type === 'scale') {
                var sx = args.length > 0 && !isNaN(args[0]) ? args[0] : 1;
                var sy = args.length > 1 && !isNaN(args[1]) ? args[1] : sx;
                m.a = sx;
                m.d = sy;
            } else if (type === 'rotate') {
                var angle = ((args[0] || 0) * Math.PI) / 180;
                var cos = Math.cos(angle);
                var sin = Math.sin(angle);
                var rot = { a: cos, b: sin, c: -sin, d: cos, e: 0, f: 0 };
                if (args.length >= 3) {
                    var cx = args[1] || 0;
                    var cy = args[2] || 0;
                    // translate(cx,cy) rotate(a) translate(-cx,-cy)
                    m = multiplyMatrices(
                        translateMatrix(cx, cy),
                        multiplyMatrices(rot, translateMatrix(-cx, -cy))
                    );
                } else {
                    m = rot;
                }
            } else if (type === 'skewX') {
                m.c = Math.tan(((args[0] || 0) * Math.PI) / 180);
            } else if (type === 'skewY') {
                m.b = Math.tan(((args[0] || 0) * Math.PI) / 180);
            }
            result = multiplyMatrices(result, m);
        }
        return result;
    }

    /** Axis-aligned bounds of a bbox after applying an affine matrix to its corners. */
    function transformBBox(bb, matrix) {
        var corners = [
            transformPoint(matrix, bb.x, bb.y),
            transformPoint(matrix, bb.x + bb.width, bb.y),
            transformPoint(matrix, bb.x, bb.y + bb.height),
            transformPoint(matrix, bb.x + bb.width, bb.y + bb.height)
        ];
        var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        for (var i = 0; i < 4; i++) {
            var p = corners[i];
            if (p.x < minX) minX = p.x;
            if (p.y < minY) minY = p.y;
            if (p.x > maxX) maxX = p.x;
            if (p.y > maxY) maxY = p.y;
        }
        return makeBBox(minX, minY, maxX - minX, maxY - minY);
    }

    function getTextAnchor(node) {
        var cur = node;
        while (cur && cur.nodeType === 1) {
            var anchor = cur.style ? (cur.style.getPropertyValue('text-anchor') || cur.getAttribute('text-anchor')) : null;
            if (anchor) return anchor.trim().toLowerCase();
            cur = cur.parentNode;
        }
        return 'start';
    }

    function makeBBox(x, y, w, h) {
        return {
            x: x,
            y: y,
            width: w,
            height: h,
            left: x,
            top: y,
            right: x + w,
            bottom: y + h
        };
    }

    function measureText(text, fontFamily, fontSize, fontWeight) {
        var w = 0, h = fontSize * 1.2, a = fontSize * 0.8, d = fontSize * 0.2;
        if (typeof globalScope._measureTextRaw === 'function') {
            try {
                var raw = globalScope._measureTextRaw(text, fontFamily, String(fontSize), fontWeight);
                var parts = raw.split(',');
                w = parseFloat(parts[0]) || 0;
                h = parseFloat(parts[1]) || (fontSize * 1.2);
                a = parseFloat(parts[2]) || (fontSize * 0.8);
                d = parseFloat(parts[3]) || (fontSize * 0.2);
            } catch (e) {
                w = text.length * fontSize * 0.6;
            }
        } else {
            w = text.length * fontSize * 0.6;
        }
        return { width: w, height: h, ascent: a, descent: d };
    }

    function textBBox(x, y, width, height, ascent, anchor) {
        var minX;
        if (anchor === 'middle') {
            minX = x - width / 2;
        } else if (anchor === 'end') {
            minX = x - width;
        } else {
            minX = x;
        }
        return makeBBox(minX, y - ascent, width, height);
    }

    // ponytail: O(n) flatten with fixed 24 samples/curve — enough for arrow
    // heads and layout; upgrade to adaptive subdivision if length accuracy matters.
    var PATH_CURVE_SAMPLES = 24;

    function distance(a, b) {
        var dx = b.x - a.x;
        var dy = b.y - a.y;
        return Math.sqrt(dx * dx + dy * dy);
    }

    function lerpPoint(a, b, t) {
        return { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t };
    }

    function cubicAt(p0, p1, p2, p3, t) {
        var mt = 1 - t;
        var mt2 = mt * mt;
        var t2 = t * t;
        return {
            x: mt2 * mt * p0.x + 3 * mt2 * t * p1.x + 3 * mt * t2 * p2.x + t2 * t * p3.x,
            y: mt2 * mt * p0.y + 3 * mt2 * t * p1.y + 3 * mt * t2 * p2.y + t2 * t * p3.y
        };
    }

    function quadAt(p0, p1, p2, t) {
        var mt = 1 - t;
        return {
            x: mt * mt * p0.x + 2 * mt * t * p1.x + t * t * p2.x,
            y: mt * mt * p0.y + 2 * mt * t * p1.y + t * t * p2.y
        };
    }

    function sampleCubic(p0, p1, p2, p3, out) {
        for (var i = 1; i <= PATH_CURVE_SAMPLES; i++) {
            out.push(cubicAt(p0, p1, p2, p3, i / PATH_CURVE_SAMPLES));
        }
    }

    function sampleQuad(p0, p1, p2, out) {
        for (var i = 1; i <= PATH_CURVE_SAMPLES; i++) {
            out.push(quadAt(p0, p1, p2, i / PATH_CURVE_SAMPLES));
        }
    }

    /** SVG F.6.5 endpoint-to-center, then sample the elliptical arc. */
    function sampleArc(p0, rx, ry, phiDeg, largeArc, sweep, p1, out) {
        rx = Math.abs(rx);
        ry = Math.abs(ry);
        if (rx === 0 || ry === 0 || (p0.x === p1.x && p0.y === p1.y)) {
            out.push({ x: p1.x, y: p1.y });
            return;
        }

        var phi = (phiDeg * Math.PI) / 180;
        var cosPhi = Math.cos(phi);
        var sinPhi = Math.sin(phi);
        var dx = (p0.x - p1.x) / 2;
        var dy = (p0.y - p1.y) / 2;
        var x1p = cosPhi * dx + sinPhi * dy;
        var y1p = -sinPhi * dx + cosPhi * dy;

        var rx2 = rx * rx;
        var ry2 = ry * ry;
        var x1p2 = x1p * x1p;
        var y1p2 = y1p * y1p;
        var lambda = x1p2 / rx2 + y1p2 / ry2;
        if (lambda > 1) {
            var s = Math.sqrt(lambda);
            rx *= s;
            ry *= s;
            rx2 = rx * rx;
            ry2 = ry * ry;
        }

        var denom = rx2 * y1p2 + ry2 * x1p2;
        var num = rx2 * ry2 - denom;
        var cRad = denom === 0 ? 0 : Math.max(0, num / denom);
        var cSign = largeArc === sweep ? -1 : 1;
        var cxp = cSign * Math.sqrt(cRad) * (rx * y1p) / ry;
        var cyp = cSign * Math.sqrt(cRad) * (-ry * x1p) / rx;

        var cx = cosPhi * cxp - sinPhi * cyp + (p0.x + p1.x) / 2;
        var cy = sinPhi * cxp + cosPhi * cyp + (p0.y + p1.y) / 2;

        function angle(ux, uy, vx, vy) {
            var dot = ux * vx + uy * vy;
            var len = Math.sqrt(ux * ux + uy * uy) * Math.sqrt(vx * vx + vy * vy);
            var ang = Math.acos(Math.max(-1, Math.min(1, len === 0 ? 0 : dot / len)));
            return ux * vy - uy * vx < 0 ? -ang : ang;
        }

        var theta1 = angle(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry);
        var dTheta = angle(
            (x1p - cxp) / rx, (y1p - cyp) / ry,
            (-x1p - cxp) / rx, (-y1p - cyp) / ry
        );
        if (!sweep && dTheta > 0) dTheta -= 2 * Math.PI;
        if (sweep && dTheta < 0) dTheta += 2 * Math.PI;

        for (var i = 1; i <= PATH_CURVE_SAMPLES; i++) {
            var t = i / PATH_CURVE_SAMPLES;
            var theta = theta1 + t * dTheta;
            var cosT = Math.cos(theta);
            var sinT = Math.sin(theta);
            out.push({
                x: cosPhi * rx * cosT - sinPhi * ry * sinT + cx,
                y: sinPhi * rx * cosT + cosPhi * ry * sinT + cy
            });
        }
    }

    /**
     * Flatten SVG path `d` into subpaths of polyline points.
     * Supports M/L/H/V/Z and samples C/S/Q/T/A.
     */
    function flattenPathData(d) {
        var subpaths = [];
        if (!d) return subpaths;

        var tokens = [];
        var re = /([MmLlHhVvCcSsQqTtAaZz])|([+-]?(?:\d*\.\d+|\d+)(?:[eE][+-]?\d+)?)/g;
        var m;
        while ((m = re.exec(String(d))) !== null) {
            tokens.push(m[1] || m[2]);
        }

        var i = 0;
        var cx = 0, cy = 0;
        var startX = 0, startY = 0;
        var lastCx = 0, lastCy = 0;
        var lastQCx = 0, lastQCy = 0;
        var lastCmd = '';
        var cur = null;

        function nextNum() {
            if (i >= tokens.length) return NaN;
            if (/^[MmLlHhVvCcSsQqTtAaZz]$/.test(tokens[i])) return NaN;
            var v = parseFloat(tokens[i]);
            if (isNaN(v)) return NaN;
            i++;
            return v;
        }

        function startSubpath(x, y) {
            cur = [{ x: x, y: y }];
            subpaths.push(cur);
            startX = x;
            startY = y;
            cx = x;
            cy = y;
        }

        function ensureSubpath() {
            if (!cur) startSubpath(cx, cy);
        }

        function addPoint(x, y) {
            ensureSubpath();
            cur.push({ x: x, y: y });
            cx = x;
            cy = y;
        }

        while (i < tokens.length) {
            var tok = tokens[i];
            var cmd;
            if (/^[MmLlHhVvCcSsQqTtAaZz]$/.test(tok)) {
                cmd = tok;
                i++;
            } else if (lastCmd) {
                // Implicit command repetition.
                if (lastCmd === 'M') cmd = 'L';
                else if (lastCmd === 'm') cmd = 'l';
                else cmd = lastCmd;
            } else {
                i++;
                continue;
            }

            var abs = cmd === cmd.toUpperCase();
            var c = cmd.toUpperCase();
            var prevCmd = lastCmd;
            lastCmd = cmd;

            if (c === 'Z') {
                if (cur && (cx !== startX || cy !== startY)) {
                    cur.push({ x: startX, y: startY });
                }
                cx = startX;
                cy = startY;
                lastCx = cx;
                lastCy = cy;
                lastQCx = cx;
                lastQCy = cy;
                continue;
            }

            if (c === 'M') {
                var mx = nextNum();
                var my = nextNum();
                if (isNaN(mx) || isNaN(my)) break;
                if (!abs) {
                    mx += cx;
                    my += cy;
                }
                startSubpath(mx, my);
                lastCx = mx;
                lastCy = my;
                lastQCx = mx;
                lastQCy = my;
                // Extra coordinate pairs after M/m are treated as L/l.
                lastCmd = abs ? 'L' : 'l';
                continue;
            }

            if (c === 'L') {
                while (true) {
                    var lx = nextNum();
                    var ly = nextNum();
                    if (isNaN(lx) || isNaN(ly)) {
                        if (!isNaN(lx)) i--;
                        break;
                    }
                    if (!abs) {
                        lx += cx;
                        ly += cy;
                    }
                    addPoint(lx, ly);
                    lastCx = cx;
                    lastCy = cy;
                    lastQCx = cx;
                    lastQCy = cy;
                }
                continue;
            }

            if (c === 'H') {
                while (true) {
                    var hx = nextNum();
                    if (isNaN(hx)) break;
                    if (!abs) hx += cx;
                    addPoint(hx, cy);
                    lastCx = cx;
                    lastCy = cy;
                    lastQCx = cx;
                    lastQCy = cy;
                }
                continue;
            }

            if (c === 'V') {
                while (true) {
                    var vy = nextNum();
                    if (isNaN(vy)) break;
                    if (!abs) vy += cy;
                    addPoint(cx, vy);
                    lastCx = cx;
                    lastCy = cy;
                    lastQCx = cx;
                    lastQCy = cy;
                }
                continue;
            }

            if (c === 'C') {
                while (true) {
                    var c1x = nextNum(), c1y = nextNum();
                    var c2x = nextNum(), c2y = nextNum();
                    var x = nextNum(), y = nextNum();
                    if (isNaN(c1x) || isNaN(c1y) || isNaN(c2x) || isNaN(c2y) || isNaN(x) || isNaN(y)) {
                        break;
                    }
                    if (!abs) {
                        c1x += cx; c1y += cy;
                        c2x += cx; c2y += cy;
                        x += cx; y += cy;
                    }
                    ensureSubpath();
                    sampleCubic({ x: cx, y: cy }, { x: c1x, y: c1y }, { x: c2x, y: c2y }, { x: x, y: y }, cur);
                    lastCx = c2x;
                    lastCy = c2y;
                    lastQCx = cx;
                    lastQCy = cy;
                    cx = x;
                    cy = y;
                }
                continue;
            }

            if (c === 'S') {
                while (true) {
                    var s2x = nextNum(), s2y = nextNum();
                    var sx = nextNum(), sy = nextNum();
                    if (isNaN(s2x) || isNaN(s2y) || isNaN(sx) || isNaN(sy)) break;
                    if (!abs) {
                        s2x += cx; s2y += cy;
                        sx += cx; sy += cy;
                    }
                    var s1x = cx;
                    var s1y = cy;
                    var prev = prevCmd.toUpperCase();
                    if (prev === 'C' || prev === 'S') {
                        s1x = 2 * cx - lastCx;
                        s1y = 2 * cy - lastCy;
                    }
                    ensureSubpath();
                    sampleCubic({ x: cx, y: cy }, { x: s1x, y: s1y }, { x: s2x, y: s2y }, { x: sx, y: sy }, cur);
                    lastCx = s2x;
                    lastCy = s2y;
                    lastQCx = cx;
                    lastQCy = cy;
                    cx = sx;
                    cy = sy;
                    prevCmd = cmd;
                }
                continue;
            }

            if (c === 'Q') {
                while (true) {
                    var q1x = nextNum(), q1y = nextNum();
                    var qx = nextNum(), qy = nextNum();
                    if (isNaN(q1x) || isNaN(q1y) || isNaN(qx) || isNaN(qy)) break;
                    if (!abs) {
                        q1x += cx; q1y += cy;
                        qx += cx; qy += cy;
                    }
                    ensureSubpath();
                    sampleQuad({ x: cx, y: cy }, { x: q1x, y: q1y }, { x: qx, y: qy }, cur);
                    lastQCx = q1x;
                    lastQCy = q1y;
                    lastCx = cx;
                    lastCy = cy;
                    cx = qx;
                    cy = qy;
                }
                continue;
            }

            if (c === 'T') {
                while (true) {
                    var tx = nextNum(), ty = nextNum();
                    if (isNaN(tx) || isNaN(ty)) break;
                    if (!abs) {
                        tx += cx;
                        ty += cy;
                    }
                    var tcx = cx;
                    var tcy = cy;
                    var prevT = prevCmd.toUpperCase();
                    if (prevT === 'Q' || prevT === 'T') {
                        tcx = 2 * cx - lastQCx;
                        tcy = 2 * cy - lastQCy;
                    }
                    ensureSubpath();
                    sampleQuad({ x: cx, y: cy }, { x: tcx, y: tcy }, { x: tx, y: ty }, cur);
                    lastQCx = tcx;
                    lastQCy = tcy;
                    lastCx = cx;
                    lastCy = cy;
                    cx = tx;
                    cy = ty;
                    prevCmd = cmd;
                }
                continue;
            }

            if (c === 'A') {
                while (true) {
                    var arx = nextNum(), ary = nextNum();
                    var aPhi = nextNum();
                    var aLarge = nextNum(), aSweep = nextNum();
                    var ax = nextNum(), ay = nextNum();
                    if (isNaN(arx) || isNaN(ary) || isNaN(aPhi) || isNaN(aLarge) || isNaN(aSweep) || isNaN(ax) || isNaN(ay)) {
                        break;
                    }
                    if (!abs) {
                        ax += cx;
                        ay += cy;
                    }
                    ensureSubpath();
                    sampleArc(
                        { x: cx, y: cy },
                        arx, ary, aPhi,
                        aLarge !== 0, aSweep !== 0,
                        { x: ax, y: ay },
                        cur
                    );
                    lastCx = cx;
                    lastCy = cy;
                    lastQCx = cx;
                    lastQCy = cy;
                    cx = ax;
                    cy = ay;
                }
                continue;
            }
        }

        return subpaths;
    }

    function pathLengthFromSubpaths(subpaths) {
        var total = 0;
        for (var s = 0; s < subpaths.length; s++) {
            var pts = subpaths[s];
            for (var i = 1; i < pts.length; i++) {
                total += distance(pts[i - 1], pts[i]);
            }
        }
        return total;
    }

    function pointAtLengthOnSubpaths(subpaths, len) {
        var total = pathLengthFromSubpaths(subpaths);
        if (subpaths.length === 0 || subpaths[0].length === 0) {
            return { x: 0, y: 0 };
        }
        if (total <= 0) {
            return { x: subpaths[0][0].x, y: subpaths[0][0].y };
        }
        if (len <= 0) {
            return { x: subpaths[0][0].x, y: subpaths[0][0].y };
        }
        if (len >= total) {
            var lastSub = subpaths[subpaths.length - 1];
            var lastPt = lastSub[lastSub.length - 1];
            return { x: lastPt.x, y: lastPt.y };
        }
        var remaining = len;
        for (var s = 0; s < subpaths.length; s++) {
            var pts = subpaths[s];
            for (var i = 1; i < pts.length; i++) {
                var segLen = distance(pts[i - 1], pts[i]);
                if (remaining <= segLen) {
                    var t = segLen === 0 ? 0 : remaining / segLen;
                    return lerpPoint(pts[i - 1], pts[i], t);
                }
                remaining -= segLen;
            }
        }
        var endSub = subpaths[subpaths.length - 1];
        var endPt = endSub[endSub.length - 1];
        return { x: endPt.x, y: endPt.y };
    }

    function bboxFromSubpaths(subpaths) {
        var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        var any = false;
        for (var s = 0; s < subpaths.length; s++) {
            var pts = subpaths[s];
            for (var i = 0; i < pts.length; i++) {
                any = true;
                if (pts[i].x < minX) minX = pts[i].x;
                if (pts[i].y < minY) minY = pts[i].y;
                if (pts[i].x > maxX) maxX = pts[i].x;
                if (pts[i].y > maxY) maxY = pts[i].y;
            }
        }
        if (!any) return makeBBox(0, 0, 0, 0);
        return makeBBox(minX, minY, maxX - minX, maxY - minY);
    }

    function lineEndpoints(el) {
        return {
            x1: parseFloat(el.getAttribute('x1')) || 0,
            y1: parseFloat(el.getAttribute('y1')) || 0,
            x2: parseFloat(el.getAttribute('x2')) || 0,
            y2: parseFloat(el.getAttribute('y2')) || 0
        };
    }

    function shapeBBox(el, tag) {
        if (tag === 'path') {
            return bboxFromSubpaths(flattenPathData(el.getAttribute('d') || ''));
        }
        if (tag === 'line') {
            var ln = lineEndpoints(el);
            var minX = Math.min(ln.x1, ln.x2);
            var minY = Math.min(ln.y1, ln.y2);
            return makeBBox(minX, minY, Math.abs(ln.x2 - ln.x1), Math.abs(ln.y2 - ln.y1));
        }
        if (tag === 'rect') {
            var rx = parseFloat(el.getAttribute('x')) || 0;
            var ry = parseFloat(el.getAttribute('y')) || 0;
            var rw = parseFloat(el.getAttribute('width')) || 0;
            var rh = parseFloat(el.getAttribute('height')) || 0;
            return makeBBox(rx, ry, rw, rh);
        }
        if (tag === 'circle') {
            var ccx = parseFloat(el.getAttribute('cx')) || 0;
            var ccy = parseFloat(el.getAttribute('cy')) || 0;
            var cr = parseFloat(el.getAttribute('r')) || 0;
            return makeBBox(ccx - cr, ccy - cr, 2 * cr, 2 * cr);
        }
        if (tag === 'ellipse') {
            var ecx = parseFloat(el.getAttribute('cx')) || 0;
            var ecy = parseFloat(el.getAttribute('cy')) || 0;
            var erx = parseFloat(el.getAttribute('rx')) || 0;
            var ery = parseFloat(el.getAttribute('ry')) || 0;
            return makeBBox(ecx - erx, ecy - ery, 2 * erx, 2 * ery);
        }
        return null;
    }

    Element.prototype.getBBox = function() {
        var tag = this.tagName.toLowerCase();
        var x = parseFloat(this.getAttribute('x')) || 0;
        var y = parseFloat(this.getAttribute('y')) || 0;

        if (tag === 'text') {
            // Check if <text> contains child <tspan> elements (e.g. multi-line text)
            var tspans = [];
            for (var i = 0; i < this.childNodes.length; i++) {
                var ch = this.childNodes[i];
                if (ch.nodeType === 1 && ch.tagName.toLowerCase() === 'tspan') {
                    tspans.push(ch);
                }
            }

            if (tspans.length > 0) {
                var parentFontSize = parseFloat(this.style.getPropertyValue('font-size') || this.getAttribute('font-size')) || 12;
                var parentFontFamily = this.style.getPropertyValue('font-family') || this.getAttribute('font-family') || 'sans-serif';
                var parentFontWeight = this.style.getPropertyValue('font-weight') || this.getAttribute('font-weight') || 'normal';
                var parentAnchor = getTextAnchor(this);
                var baseX = x;
                var baseY = y;

                var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
                var curY = baseY;

                for (var j = 0; j < tspans.length; j++) {
                    var tsp = tspans[j];
                    var tText = tsp.textContent || '';
                    var tFontSize = parseFloat(tsp.style.getPropertyValue('font-size') || tsp.getAttribute('font-size')) || parentFontSize;
                    var tFontFamily = tsp.style.getPropertyValue('font-family') || tsp.getAttribute('font-family') || parentFontFamily;
                    var tFontWeight = tsp.style.getPropertyValue('font-weight') || tsp.getAttribute('font-weight') || parentFontWeight;
                    var tAnchor = (tsp.style.getPropertyValue('text-anchor') || tsp.getAttribute('text-anchor') || parentAnchor).trim().toLowerCase();

                    var tx = tsp.hasAttribute('x') ? (parseFloat(tsp.getAttribute('x')) || 0) : baseX;
                    if (tsp.hasAttribute('y')) {
                        curY = parseFloat(tsp.getAttribute('y')) || 0;
                    }
                    if (tsp.hasAttribute('dy')) {
                        var dyStr = tsp.getAttribute('dy') || '';
                        var dyVal = 0;
                        if (dyStr.indexOf('em') !== -1) {
                            dyVal = parseFloat(dyStr) * tFontSize;
                        } else {
                            dyVal = parseFloat(dyStr) || 0;
                        }
                        curY += dyVal;
                    }

                    var tm = measureText(tText, tFontFamily, tFontSize, tFontWeight);
                    var tbb = textBBox(tx, curY, tm.width, tm.height, tm.ascent, tAnchor);
                    if (tbb.x < minX) minX = tbb.x;
                    if (tbb.y < minY) minY = tbb.y;
                    if (tbb.right > maxX) maxX = tbb.right;
                    if (tbb.bottom > maxY) maxY = tbb.bottom;
                }

                if (minX !== Infinity) {
                    return makeBBox(minX, minY, maxX - minX, maxY - minY);
                }
            }
        }

        if (tag === 'text' || tag === 'tspan') {
            var text = this.textContent || '';
            var fontSize = parseFloat(this.style.getPropertyValue('font-size') || this.getAttribute('font-size')) || 12;
            var fontFamily = this.style.getPropertyValue('font-family') || this.getAttribute('font-family') || 'sans-serif';
            var fontWeight = this.style.getPropertyValue('font-weight') || this.getAttribute('font-weight') || 'normal';
            var m = measureText(text, fontFamily, fontSize, fontWeight);
            return textBBox(x, y, m.width, m.height, m.ascent, getTextAnchor(this));
        }

        var shapeBB = shapeBBox(this, tag);
        if (shapeBB) return shapeBB;

        // For groups (<g>, <svg>), aggregate children bounding boxes.
        // Each child's transform is applied to its bbox corners (SVG getBBox on a
        // group includes child transforms; an element's own transform is NOT part
        // of that element's own getBBox).
        var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        var hasKids = false;
        for (var i = 0; i < this.childNodes.length; i++) {
            var child = this.childNodes[i];
            if (child.nodeType === 1 && typeof child.getBBox === 'function') {
                var bb = child.getBBox();
                var childMatrix = parseTransform(child.getAttribute('transform'));
                var transformed = transformBBox(bb, childMatrix);
                var cw = transformed.width;
                var ch = transformed.height;
                if (cw > 0 || ch > 0) {
                    hasKids = true;
                    if (transformed.x < minX) minX = transformed.x;
                    if (transformed.y < minY) minY = transformed.y;
                    if (transformed.x + cw > maxX) maxX = transformed.x + cw;
                    if (transformed.y + ch > maxY) maxY = transformed.y + ch;
                }
            }
        }
        if (!hasKids) {
            return makeBBox(0, 0, 0, 0);
        }
        return makeBBox(minX, minY, maxX - minX, maxY - minY);
    };

    Element.prototype.getBoundingClientRect = function() {
        var bb = this.getBBox();
        // Compose full ancestor matrices (including this element's transform).
        // Walk self → root so final = T_root * ... * T_parent * T_self.
        var matrix = identityMatrix();
        var cur = this;
        while (cur && cur.nodeType === 1) {
            var local = cur.getAttribute
                ? parseTransform(cur.getAttribute('transform'))
                : identityMatrix();
            var ox = cur.offsetLeft || 0;
            var oy = cur.offsetTop || 0;
            if (ox || oy) {
                local = multiplyMatrices(translateMatrix(ox, oy), local);
            }
            matrix = multiplyMatrices(local, matrix);
            cur = cur.parentNode;
        }
        var transformed = transformBBox(bb, matrix);
        // Prefer explicit layout size when present (HTML elements); otherwise use
        // the transformed SVG bbox so rotations expand width/height correctly.
        var width = this.offsetWidth || this.clientWidth || transformed.width;
        var height = this.offsetHeight || this.clientHeight || transformed.height;
        return {
            left: transformed.x,
            top: transformed.y,
            right: transformed.x + width,
            bottom: transformed.y + height,
            width: width,
            height: height
        };
    };

    Element.prototype.getComputedTextLength = function() {
        return this.getBBox().width;
    };

    Element.prototype.getTotalLength = function() {
        var tag = this.tagName.toLowerCase();
        if (tag === 'path') {
            return pathLengthFromSubpaths(flattenPathData(this.getAttribute('d') || ''));
        }
        if (tag === 'line') {
            var ln = lineEndpoints(this);
            return distance({ x: ln.x1, y: ln.y1 }, { x: ln.x2, y: ln.y2 });
        }
        var bb = this.getBBox();
        var p = (bb.width + bb.height) * 2;
        return p > 0 ? p : 100;
    };

    Element.prototype.getPointAtLength = function(len) {
        var tag = this.tagName.toLowerCase();
        if (tag === 'path') {
            return pointAtLengthOnSubpaths(flattenPathData(this.getAttribute('d') || ''), len);
        }
        if (tag === 'line') {
            var ln = lineEndpoints(this);
            var p0 = { x: ln.x1, y: ln.y1 };
            var p1 = { x: ln.x2, y: ln.y2 };
            var total = distance(p0, p1);
            if (total <= 0) return { x: p0.x, y: p0.y };
            if (len <= 0) return { x: p0.x, y: p0.y };
            if (len >= total) return { x: p1.x, y: p1.y };
            return lerpPoint(p0, p1, len / total);
        }
        var bb = this.getBBox();
        return { x: bb.x, y: bb.y };
    };

    var SVG_CAMEL_TAGS = {
        'lineargradient': 'linearGradient',
        'radialgradient': 'radialGradient',
        'clippath': 'clipPath',
        'textpath': 'textPath',
        'foreignobject': 'foreignObject',
        'animatetransform': 'animateTransform',
        'fecolormatrix': 'feColorMatrix',
        'fecomposite': 'feComposite',
        'fegaussianblur': 'feGaussianBlur',
        'femerge': 'feMerge',
        'femergenode': 'feMergeNode',
        'feoffset': 'feOffset'
    };

    // Serialization
    function serializeNode(node) {
        if (node.nodeType === 3) {
            return node.nodeValue
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
        }
        if (node.nodeType === 1) {
            var lowerTag = node.tagName.toLowerCase();
            var tag = SVG_CAMEL_TAGS[lowerTag] || lowerTag;
            var out = '<' + tag;
            var css = (node.style && typeof node.style.cssText === 'function') ? node.style.cssText() : '';
            for (var k in node._attributes) {
                if (k === 'style') continue;
                out += ' ' + k + '="' + String(node._attributes[k]).replace(/"/g, '&quot;') + '"';
            }
            if (css) {
                out += ' style="' + css.replace(/"/g, '&quot;') + '"';
            } else if (node._attributes['style']) {
                out += ' style="' + String(node._attributes['style']).replace(/"/g, '&quot;') + '"';
            }
            if (node.childNodes.length === 0) {
                if (['circle', 'path', 'line', 'rect', 'polygon', 'polyline', 'ellipse'].indexOf(lowerTag) !== -1) {
                    return out + '/>';
                }
                return out + '></' + tag + '>';
            }
            out += '>';
            for (var i = 0; i < node.childNodes.length; i++) {
                out += serializeNode(node.childNodes[i]);
            }
            out += '</' + tag + '>';
            return out;
        }
        return '';
    }

    Object.defineProperty(Element.prototype, 'outerHTML', {
        get: function() { return serializeNode(this); }
    });
    Object.defineProperty(Element.prototype, 'innerHTML', {
        get: function() {
            var out = '';
            for (var i = 0; i < this.childNodes.length; i++) {
                out += serializeNode(this.childNodes[i]);
            }
            return out;
        },
        set: function(html) {
            this.childNodes = [];
            // Basic text assignment if no parser needed
            if (html && html.indexOf('<') === -1) {
                this.appendChild(new Text(html));
            }
        }
    });

    // --- HTML / SVG Specifics ---
    function HTMLElement(tagName) { Element.call(this, tagName, null); }
    HTMLElement.prototype = Object.create(Element.prototype);

    function SVGElement(tagName) { Element.call(this, tagName, 'http://www.w3.org/2000/svg'); }
    SVGElement.prototype = Object.create(Element.prototype);

    function HTMLStyleElement() {
        HTMLElement.call(this, 'style');
        this.sheet = {
            insertRule: function(rule, index) {},
            addRule: function(selector, style, index) {},
            cssRules: []
        };
    }
    HTMLStyleElement.prototype = Object.create(HTMLElement.prototype);

    function HTMLCanvasElement() {
        HTMLElement.call(this, 'canvas');
        this._width = 300;
        this._height = 150;
        this._ctx2d = null;
    }
    HTMLCanvasElement.prototype = Object.create(HTMLElement.prototype);
    Object.defineProperty(HTMLCanvasElement.prototype, 'width', {
        get: function() { return this._width; },
        set: function(v) {
            this._width = parseInt(v, 10) || 0;
            this.setAttribute('width', this._width);
            if (this._ctx2d) { this._ctx2d._commands = []; }
        }
    });
    Object.defineProperty(HTMLCanvasElement.prototype, 'height', {
        get: function() { return this._height; },
        set: function(v) {
            this._height = parseInt(v, 10) || 0;
            this.setAttribute('height', this._height);
            if (this._ctx2d) { this._ctx2d._commands = []; }
        }
    });
    HTMLCanvasElement.prototype.getContext = function(type) {
        if (type === '2d') {
            if (!this._ctx2d) {
                var self = this;
                this._ctx2d = {
                    canvas: self,
                    fillStyle: '#000000',
                    strokeStyle: '#000000',
                    lineWidth: 1,
                    _commands: [],
                    fillRect: function(x, y, w, h) {
                        this._commands.push({
                            op: 'fillRect',
                            x: x,
                            y: y,
                            w: w,
                            h: h,
                            fill: this.fillStyle
                        });
                    },
                    clearRect: function(x, y, w, h) {
                        this._commands.push({
                            op: 'clearRect',
                            x: x,
                            y: y,
                            w: w,
                            h: h
                        });
                    },
                    save: function() {},
                    restore: function() {},
                    beginPath: function() {},
                    closePath: function() {},
                    moveTo: function() {},
                    lineTo: function() {},
                    stroke: function() {},
                    fill: function() {}
                };
            }
            return this._ctx2d;
        }
        return null;
    };
    HTMLCanvasElement.prototype.toDataURL = function(type) {
        if (typeof globalScope._encodeCanvasToPNG === 'function') {
            var cmds = this._ctx2d ? this._ctx2d._commands : [];
            return globalScope._encodeCanvasToPNG(this.width, this.height, JSON.stringify(cmds));
        }
        return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=';
    };

    // --- Document ---
    function Document() {
        Node.call(this);
        this.nodeType = 9;
        this.nodeName = '#document';
        this._ownerDoc = null;
        this.documentElement = new HTMLElement('html');
        this.documentElement._ownerDoc = this;
        this.head = new HTMLElement('head');
        this.head._ownerDoc = this;
        this.body = new HTMLElement('body');
        this.body._ownerDoc = this;
        this.documentElement.appendChild(this.head);
        this.documentElement.appendChild(this.body);
    }
    Document.prototype = Object.create(Node.prototype);

    Document.prototype.createElement = function(tag) {
        var lower = String(tag).toLowerCase();
        var el;
        if (lower === 'style') el = new HTMLStyleElement();
        else if (lower === 'canvas') el = new HTMLCanvasElement();
        else el = new HTMLElement(lower);
        el.ownerDocument = this;
        return el;
    };

    Document.prototype.createElementNS = function(ns, tag) {
        var lower = String(tag).toLowerCase();
        var el = new SVGElement(lower);
        el.namespaceURI = ns;
        el.ownerDocument = this;
        return el;
    };

    Document.prototype.createTextNode = function(text) {
        var t = new Text(text);
        t.ownerDocument = this;
        return t;
    };

    Document.prototype.createDocumentFragment = function() {
        var frag = new DocumentFragment();
        frag.ownerDocument = this;
        return frag;
    };

    Document.prototype.getElementById = function(id) {
        return this.documentElement.querySelector('#' + id);
    };

    Document.prototype.querySelector = function(sel) {
        return this.documentElement.querySelector(sel);
    };

    Document.prototype.querySelectorAll = function(sel) {
        return this.documentElement.querySelectorAll(sel);
    };

    Document.prototype.getElementsByTagName = function(tag) {
        return this.documentElement.getElementsByTagName(tag);
    };

    Document.prototype.getElementsByClassName = function(cls) {
        return this.documentElement.getElementsByClassName(cls);
    };

    // --- Global Setup ---
    globalScope.console = {
        log: function() {
            if (typeof globalScope._printLog === 'function') {
                globalScope._printLog(Array.prototype.slice.call(arguments).map(String).join(' '));
            }
        },
        warn: function() {
            if (typeof globalScope._printLog === 'function') {
                globalScope._printLog('[WARN] ' + Array.prototype.slice.call(arguments).map(String).join(' '));
            }
        },
        error: function() {
            if (typeof globalScope._printLog === 'function') {
                globalScope._printLog('[ERROR] ' + Array.prototype.slice.call(arguments).map(String).join(' '));
            }
        }
    };

    var doc = new Document();
    globalScope.window = globalScope;
    globalScope.self = globalScope;
    globalScope.document = doc;
    globalScope.Node = Node;
    globalScope.Element = Element;
    globalScope.HTMLElement = HTMLElement;
    globalScope.HTMLCanvasElement = HTMLCanvasElement;
    globalScope.SVGElement = SVGElement;
    globalScope.DocumentFragment = DocumentFragment;
    globalScope.Text = Text;

    globalScope.Event = function(type) { this.type = type; };
    globalScope.CustomEvent = function(type, p) { this.type = type; this.detail = p ? p.detail : null; };
    globalScope.MouseEvent = function(type) { this.type = type; };

    globalScope.DOMParser = function() {};
    globalScope.DOMParser.prototype.parseFromString = function(str, mime) {
        var d = new Document();
        var root = new SVGElement('svg');
        d.appendChild(root);
        return d;
    };

    globalScope.XMLSerializer = function() {};
    globalScope.XMLSerializer.prototype.serializeToString = function(node) {
        return serializeNode(node);
    };

    globalScope.getComputedStyle = function(el) {
        return el ? el.style : new CSSStyleDeclaration();
    };

    globalScope.setTimeout = function(fn, ms) { return 1; };
    globalScope.clearTimeout = function(id) {};
    globalScope.setInterval = function(fn, ms) { return 1; };
    globalScope.clearInterval = function(id) {};
    globalScope.requestAnimationFrame = function(fn) {
        try { fn(Date.now()); } catch(e) {}
        return 1;
    };
    globalScope.cancelAnimationFrame = function(id) {};

    globalScope.navigator = {
        userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)",
        platform: "MacIntel"
    };

    globalScope.location = {
        href: "http://localhost/",
        protocol: "http:",
        host: "localhost",
        pathname: "/"
    };

    globalScope.screen = { width: 1920, height: 1080 };

})();
