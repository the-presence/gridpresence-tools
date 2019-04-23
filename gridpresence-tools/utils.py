#!/usr/bin/env python
'''Useful unencapsulated functions to be reused across the domain.'''
from __future__ import print_function

import os
import errno
from subprocess import check_output

DEBUG = False

def debug(string):
    if DEBUG is True:
        print(string)

def shell_cmd(cspec):
    '''Executes a shell command and returns a string list of the output.'''
    debug('Executing: {0}'.format(cspec))
    intermed = check_output(cspec).decode('utf-8').rstrip()
    retval = intermed.split('\n')
    return retval

def utf8(array):
    '''Preserves byte strings, converts Unicode into UTF-8.'''
    retval = None
    if isinstance(array, bytes) is True:
        # No need to convert in this case
        retval = array
    else:
        retval = array.encode('utf-8')
    return retval

def mkdirhier(path):
    '''Replicates mkdir -p functionality where, for a given path,
    any missing directories are created to ensure the full path exists

    Args:
        path (str): absolute path to the target directory.

    Raises:
        OSError : if the path already exists as a file, or the target directory
        cannot be created because of a permissions error.'''
    try:
        # Try to make all the necessary missing directories in the given path
        os.makedirs(path)
    except OSError as exc:
        # If the directory already exists on this path, that's okay
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        # Otherwise, it's either just a file or there's a permissions problem
        else:
            raise

def bash_var(variable):
    '''Turns a VAR into the string ${VAR} so that it can be used
    directly without confusing the string.format() template processor.'''
    return '${' + variable + '}'

def retuple(struct):
    '''Function reconstructs tuples in the flattened list-only JSON persistence structure returned
    by json-load().

    Args:
        struct : single key dictionary where the value is a list of 2 elements
        e.g. { 'key' : ['val1', 'val2'] }

    Returns:
        tuple dictionary : single key dictionary whose value is a list of one 2-element tuples
        e.g. { 'key' : [('val1', 'val2')] }

    TODO: possibly extend this out to retuple lists of general length N'''
    # We are going to return a dictionary
    retval = {}
    # There should be only 1 key in the dictionary under examination.
    # More than one could be supported, but, for now,
    # the scenario is only appended to the first
    key = struct.keys()[0]
    # The value of that key/value pair is a list
    vallist = struct[key]
    # We have to create a new list
    newlist = []
    # Each list item in vallist is a list
    for sublist in vallist:
        # Convert the 2 item list into a 2 item tuple and add it to the new list
        newlist.extend([(sublist[0], sublist[1])])
    # Create a new dictionary which replaces the original list of lists with a list of tuples
    retval[key] = newlist
    return retval

def macaddress_from_hubid(hubid):
    '''Conversion function to obtain a MAC address from a quoted Hub ID -
    as per: https://wiki.cam.uk.alertme.com/index.php/Convert_hub_text

    This conversion assumes the historic address range

    Args:
        hubid (str) : expressed in XXX-nnn format (e.g. MVC-341)

    Returns:
        macaddress (str) : expressed in XX:XX:XX:XX:XX:XX format'''
    mac=0x1c2b000000+int(''.join(reversed(['%0.2X'%((ord(x)-ord('A'))*10+ord(y)-ord('0')) for x,y in zip(*[list(x) for x in hubid.split('-')])])),16)^0xb77925
    interval = hex(mac)[2:]
    decomp = [interval[0:2].upper()+':',
              interval[2:4].upper()+':',
              interval[4:6].upper()+':',
              interval[6:8].upper()+':',
              interval[8:10].upper()]
    retval = '00:' + decomp[0]+decomp[1]+decomp[2]+decomp[3]+decomp[4]
    return retval

def hubid_from_macaddress(macaddr):
    '''Conversion function to obtain a Hub ID from a quoted MAC address -
    as per: https://wiki.cam.uk.alertme.com/index.php/Convert_hub_text

    This conversion assumes the historic address range

    Args:
        macaddr (str) : expressed in XX:XX:XX:XX:XX:XX format

    Returns:
        hubid (str) : expressed in XXX-nnn format (e.g. MVC-341)'''
    mac = [int(i, 16) for i in macaddr.split(':')]
    ascii_offset = ord('A')
    # Integer division for Python 3.x is now '//'
    retval = '%c%c%c-%d%d%d' % (chr((mac[5] ^ 0x25) // 10 + ascii_offset),
                                chr((mac[4] ^ 0x79) // 10 + ascii_offset),
                                chr((mac[3] ^ 0xB7) // 10 + ascii_offset),
                                (mac[5] ^ 0x25) % 10,
                                (mac[4] ^ 0x79) % 10,
                                (mac[3] ^ 0xB7) % 10)
    return retval

def eui64_from_macaddress(macaddr):
    '''This function converts a MAC Address to EUI64 address, often referred to as a Node ID.

    These are used as keys to hubs within the Platform messaging and database environments.

    Args:
        macaddr (str) : expressed in XX:XX:XX:XX:XX:XX format

    Returns:
       node id (str) : expressed in ::2xx:xxff:fexx:xxxx format
           (note - lowercase alpha characters throughout)

    '''
    maclower = macaddr.lower()
    macfrags = maclower.split(':')
    retval = '::2{0}:{1}ff:fe{2}:{3}{4}'.format(macfrags[1],
                                                macfrags[2],
                                                macfrags[3],
                                                macfrags[4],
                                                macfrags[5])
    return retval


# Inpsect a class/function/method's signature for default values.
# (Classes apparently use fall back to their __init__.)
# This is useful when, e.g., optional command line parameters might be used,
# but you don't want to allow for every combination.
# This returns a dict, which then can be updated with a dict of
# supplied command line parameters, and the defaults will be correct.
# If a parameter has no default, it will not appear in the result.
def get_default_args(func):
    '''Get the list of parameter defaults from a method

    Args:
        func: the function or method or class

    Return:
        A dict of key/value pairs where the default exists
    '''
    import inspect
    signature = inspect.signature(func)
    return {
        key: val.default
        for key, val in signature.parameters.items()
        if val.default is not inspect.Parameter.empty
    }


def get_args(func):
    '''Get the list of parameters from a method

    Args:
        func: the function or method or class

    Return:
        A dict of keys, with the values set to 1,
        regardless of whether a default has been defined.
    '''
    signature = inspect.signature(func)
    return {
        key: 1
        for key, val in signature.parameters.items()
    }


def myself(level=0):
    '''Report the name of a function within the function body.

    This is normally not allowed, because the function object hasn't been created yet.

    Args:
        level: the call tree level, 0 for the current method (integer)

    Returns:
        function name (string)
    '''
    import sys
    # Because this is a method in its own right, the caller's level is +1
    return sys._getframe(level + 1).f_code.co_name


def time_elapsed(time1, time2):
    ''' Return elapsed time between time1 (earlier), time2 in msec

    time1, time2: seconds since the epoch (float)
    '''
    # get timedelta
    time_diff = time2 - time1
    # convert to milliseconds, rounded to the nearest millisecond
    msec = seconds_to_milliseconds(time_diff)
    return msec


def now_inn_milliseconds():
    '''Get UTC time from datetime, convert to epoch time in msecs.
    '''
    import time
    from datetime import datetime
    return seconds_to_milliseconds(time.mktime(datetime.utcnow()))


def seconds_to_milliseconds(timestamp):
    '''Convert an epoch time in seconds to milliseconds

    Parameters:
        timestamp: Time in seconds (float or int)

    Returns:
        time in milliseconds (int)
    '''
    return int(round(timestamp) * MILLISECONDS_PER_SECOND)


def suppress_exceptions(method, exceptions_to_raise=None, report_ignored=None, *args, **kwargs):
    '''
    Suppress all exceptions from a method call.

    Parameters:
        method: method to call
        exceptions_to_raise: tuple of exceptions to raise
        report_ignored: report ignored exceptions (boolean)
        args: positional arguments to method
        kwargs: keyword arguments to method

    Return:
        result of method call
    '''

    try:
        result = method(*args, **kwargs)
        return result
    except exceptions_to_raise:
        raise
    except Exception as exc: # pylint: disable=bare-except
        if report_ignored:
            logger = logging.getLogger(method.__name__)
            logger.info('Ignoring exception %s', exc)


from hdacore.commonconstants import TIME_FORMAT_STRING
def utc_timestamp(some_time, time_format=TIME_FORMAT_STRING):
    '''Return the current UTC time, formatted by the given string.

    Args:
        some_time: a datetime object (e.g., from datetime.utcnow())
        timestamp_format: format to covert a datetime object to string

    Returns:
        A timestamp string
    '''
    if some_time is None:
        return None
    time_string = some_time.strftime(time_format)
    return time_string

def day_of_week(date):
    '''Returns a string with the name of the day of the week when passed a datetime object as input.'''
    days = ['Monday',
            'Tuesday',
            'Wednesday',
            'Thursday',
            'Friday',
            'Saturday',
            'Sunday']
    return days[date.weekday()]


class ChunkException(Exception):
    '''Exception in the chunker function
    '''
    pass


def chunker(seq, size, fill=None, complain=False):
    '''Partition a list into N parts, optionally fill any shortfall or raise an error.

    Args:
        seq: the list
        size: the chunk size
        fill: the value to use if size does not divide evenly into the list
        complain: a shortfall causes an exception to be raised

    Returns:
        a list of lists
    '''
    result = []
    for pos in range(0, len(seq), size):
        chunked = seq[pos:pos + size]
        if len(chunked) != size:
            if complain:
                raise ChunkException('size({}) does not divide list({}) evenly'.format(size, len(seq)))
            chunked.append(*[fill]*(size-len(chunked)))
        result.append(chunked)
    return result


def dynamic_import(module, ids=None):
    '''Attempt to import elements from package.module.

    This is similar to:
        from package.module import imports

    NB: hack for __import__():
    When the fromlist is empty, only the top level (i.e., package) name is returned by __import__.
    To 'Do What I Mean', a dummy module object is requested ('__file__').

    Args:
        module: The module or package name, absolute or relative.
            e.g., 'spam' or 'spam.ham.'
        ids: A list of identifiers (strings) to import from module.
            e.g., 'MyClass' or 'my_method' or 'some_list' or ['one', 'two', 'three']
            If no ids are given, the module object is returned.

    Returns:
        The identifiers as a list.
        If no identifiers were requested, the module as a list.
    '''
    if (ids is not None) and (not isinstance(ids, (list, tuple))):
        ids = [ids]

    try:
        # If len(ids) is not 1, this returns the module.
        # If len(ids) is 1, this returns the id (e.g., class)
        if ids is None:
            # dummy fromlist to get the module, and not just the package
            mod = __import__(module, fromlist=['__file__'])
            idx = [mod]
        else:
            mod = __import__(module, fromlist=ids)
            idx = [getattr(mod, idq, None) for idq in ids]
    except ImportError as exc:
        import logging
        logging.getLogger().error('Could not import {}.{}, {}'.format(module, ids, exc))
        raise
    except Exception as exc:  # report any 'loose' exceptions for diagnosis !
        import logging
        logging.getLogger().error('Unexpected error ({})'.format(exc))
        raise
    return idx


def attr_to_dict(knobject, exclude=None):
    '''Return the attributes of an object as a dict.
    Excludes methods.

    Args:
        knobject: the object instance to work from
        exclude: A regex pattern to use for excluding attributes by name.
            For instance, to exclude private attributes starting with '_', use r'^_'.
    '''
    attr_dict = {}
    for attr in dir(knobject):
        if not (exclude and re.search(exclude, attr)) and not callable(getattr(knobject, attr)):
            attr_dict[attr] = getattr(knobject, attr)
    return attr_dict

def filtered_list(inlist, fstring):
    '''Takes a string list and filters out any containing the specified
    substring returning a new subset list.'''
    outlist = []
    for item in inlist:
        if fstring in item:
            pass
        else:
            outlist.append(item)
    return outlist

def selected_list(inlist, sstring):
    '''Takes a string list and selects any containing the specified
    substring returning a new subset list.'''
    outlist = []
    for item in inlist:
        if sstring in item:
            outlist.append(item)
    return outlist


if __name__ == '__main__':
    # unit tests
    import logging
    from hdacore.logutils import logFilename, logConfigure
    LOGGER = logConfigure(logFilename())

    # dynamicImport
    # import top-level package
    HDA = dynamicImport('hdacore')
    LOGGER.info('{}=({})'.format('hda', HDA[0]))

    # import constant from submodule
    MAM = dynamicImport('hdacore.commonconstants', 'MAC_ADDRESS_MATCH')
    LOGGER.info('{}=({})'.format('MAC_ADDRESS_MATCH', MAM[0]))

    # import submodule
    BBB = dynamicImport('hdacore.commonconstants')
    LOGGER.info('{}=({})'.format('hdacore.commonconstants', BBB[0]))

    # import submodule as 'from x import y'
    CCC = dynamicImport('hdacore', 'commonconstants')
    LOGGER.info('{}=({})'.format('commonconstants', CCC[0]))

    # access constant in submodule is accessible without explicit import
    MILLISECONDS_PER_SECOND = getattr(CCC[0], 'MILLISECONDS_PER_SECOND', None)
    LOGGER.info('{}=({})'.format('MILLISECONDS_PER_SECOND', MILLISECONDS_PER_SECOND))

    # import class from submodule as 'from x import y', instantiate
    SUPPORT_KLASS = dynamicImport('hdacore.support', 'SupportedListType')
    SUPPORT = SUPPORT_KLASS[0]()
    LOGGER.info('{}=({})'.format('SUPPORT', SUPPORT))

    # timestamp
    from datetime import datetime
    LOGGER.info('Current time: ({})'.format(UtcTimeStamp(datetime.utcnow())))

    LOGGER.info('Done!')





